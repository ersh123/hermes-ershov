from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from hermes_dreaming.artifact import DreamArtifact, DreamProposal, SourceSnapshot, load_artifact, write_artifact
from hermes_dreaming.cli import main
from hermes_dreaming.commands.install_cron import DEFAULT_SCHEDULE, JOB_NAME, handle as install_cron_handle


def _write_source_tree(root: Path) -> Path:
    sources = root / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    (sources / "session-1.md").write_text(
        "# Session 1\n\nDREAM: memory: Keep updates short and concrete.\nDREAM: fact: {\"type\": \"preference\", \"key\": \"tone\", \"value\": \"casual\"}\n",
        encoding="utf-8",
    )
    return sources


def _write_artifact(artifact_root: Path, *, artifact_id: str, status: str) -> Path:
    artifact = DreamArtifact(
        artifact_id=artifact_id,
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status=status,
        workspace_root=str(artifact_root),
        source_roots=[str(artifact_root / "sources")],
        report="# Report\n",
        sources=[
            SourceSnapshot(
                path="sources/session-1.md",
                kind="session",
                content="DREAM: memory: Keep updates short and concrete.\n",
                sha256="f" * 64,
                line_count=1,
            )
        ],
        proposals=[
            DreamProposal(
                id=f"{artifact_id}-proposal",
                target_kind="memory",
                target_path="memory.md",
                mode="append_text",
                summary="append memory note",
                provenance=["sources/session-1.md:1"],
                proposed_text="- Keep updates short and concrete.",
                approved=True,
            )
        ],
    )
    artifact_dir = artifact_root / artifact_id
    write_artifact(artifact, artifact_dir)
    return artifact_dir


def test_review_command_stages_artifact_without_touching_live_files(tmp_path: Path, capsys) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    (live_root / "memory.md").write_text("# MEMORY\n", encoding="utf-8")
    (live_root / "user.md").write_text("# USER\n", encoding="utf-8")
    (live_root / "skills").mkdir()
    (live_root / "skills" / "review.md").write_text("# Review\n", encoding="utf-8")

    sources = _write_source_tree(tmp_path)
    artifact_root = tmp_path / "artifacts"

    assert (
        main(
            [
                "review",
                "--live-root",
                str(live_root),
                "--artifact-root",
                str(artifact_root),
                "--source",
                str(sources),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    artifact_dir = Path(output.splitlines()[0].split(":", 1)[1].strip())
    artifact = load_artifact(artifact_dir)

    assert artifact_dir.exists()
    assert artifact.status == "staged"
    assert "dry-run" in output.lower() or "review" in output.lower()
    assert (live_root / "memory.md").read_text(encoding="utf-8") == "# MEMORY\n"
    assert (live_root / "user.md").read_text(encoding="utf-8") == "# USER\n"


def test_compact_command_moves_terminal_artifacts_into_archive(tmp_path: Path, capsys) -> None:
    artifact_root = tmp_path / "artifacts"
    archive_root = tmp_path / "archive"
    artifact_root.mkdir()

    staged_dir = _write_artifact(artifact_root, artifact_id="artifact-staged", status="staged")
    applied_dir = _write_artifact(artifact_root, artifact_id="artifact-applied", status="applied")
    discarded_dir = _write_artifact(artifact_root, artifact_id="artifact-discarded", status="discarded")

    assert (
        main(
            [
                "compact",
                "--artifact-root",
                str(artifact_root),
                "--archive-root",
                str(archive_root),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "archived" in output.lower() or "moved" in output.lower()
    assert staged_dir.exists()
    assert not applied_dir.exists()
    assert not discarded_dir.exists()
    assert (archive_root / "artifact-applied").exists()
    assert (archive_root / "artifact-discarded").exists()
    assert load_artifact(archive_root / "artifact-applied").status == "applied"
    assert load_artifact(archive_root / "artifact-discarded").status == "discarded"


def test_install_cron_registers_review_job_idempotently() -> None:
    mock_cron = MagicMock()
    mock_cron.list_jobs.return_value = []
    mock_cron.create_job.return_value = {
        "id": "job-123",
        "name": JOB_NAME,
        "schedule_display": "At 03:00 every day",
        "next_run_at": "2099-01-02T03:00:00+00:00",
    }

    with patch.dict("sys.modules", {"cron.jobs": mock_cron}):
        result = install_cron_handle()

    assert "registered" in result.lower()
    call_kwargs = mock_cron.create_job.call_args.kwargs
    assert call_kwargs["prompt"] == "/dreaming review"
    assert call_kwargs["schedule"] == DEFAULT_SCHEDULE
    assert call_kwargs["name"] == JOB_NAME
    assert call_kwargs["deliver"] == "local"


def test_install_cron_reuses_existing_job() -> None:
    mock_cron = MagicMock()
    mock_cron.list_jobs.return_value = [
        {
            "id": "job-existing",
            "name": JOB_NAME,
            "schedule_display": "At 03:00 every day",
            "enabled": True,
            "next_run_at": "2099-01-02T03:00:00+00:00",
        }
    ]

    with patch.dict("sys.modules", {"cron.jobs": mock_cron}):
        result = install_cron_handle()

    assert "Already installed" in result
    mock_cron.create_job.assert_not_called()
