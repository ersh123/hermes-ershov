from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from hermes_dreaming.artifact import DreamArtifact, DreamProposal, SourceSnapshot, load_artifact, write_artifact
from hermes_dreaming.cli import main


def _write_source_tree(root: Path) -> Path:
    sources = root / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    (sources / "session-1.md").write_text(
        "# Session 1\n\nDREAM: memory: Keep updates short and concrete.\nDREAM: fact: {\"type\": \"preference\", \"key\": \"tone\", \"value\": \"casual\"}\nDREAM: skill: path=skills/review.md | Preserve review gates and backups.\n",
        encoding="utf-8",
    )
    return sources


def _write_report_card_artifact(root: Path, *, status: str = "staged") -> Path:
    artifact = DreamArtifact(
        artifact_id="artifact-report-card",
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status=status,
        workspace_root=str(root),
        source_roots=[str(root / "sources")],
        report="# report\nprivate report body: TOP-SECRET-REPORT\n",
        sources=[
            SourceSnapshot(
                path="sources/session-1.md",
                kind="session",
                content="DREAM: memory: TOP-SECRET-SOURCE\n",
                sha256=sha256(b"DREAM: memory: TOP-SECRET-SOURCE\n").hexdigest(),
                line_count=1,
            )
        ],
        proposals=[
            DreamProposal(
                id="proposal-memory",
                target_kind="memory",
                target_path="memory.md",
                mode="append_text",
                summary="TOP-SECRET-PROPOSAL-SUMMARY",
                provenance=["sources/session-1.md:1"],
                proposed_text="- TOP-SECRET-PROPOSAL-TEXT",
                approved=True,
            )
        ],
        validation_errors=["source bundle needs review"],
        applied_proposal_ids=["proposal-memory"] if status == "applied" else [],
        backup_paths=[str(root / "backups" / "memory.md")] if status == "applied" else [],
        applied_at="2026-05-25T13:00:00Z" if status == "applied" else None,
        discarded_at="2026-05-25T14:00:00Z" if status == "discarded" else None,
    )
    artifact_dir = root / artifact.artifact_id
    write_artifact(artifact, artifact_dir)
    return artifact_dir



def test_create_validate_apply_and_status_command_flow(tmp_path: Path, capsys) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    (live_root / "memory.md").write_text("# MEMORY\n", encoding="utf-8")
    (live_root / "user.md").write_text("# USER\n", encoding="utf-8")
    (live_root / "skills").mkdir()
    (live_root / "skills" / "review.md").write_text("# Review\n", encoding="utf-8")
    sources = _write_source_tree(tmp_path)
    artifact_root = tmp_path / "artifacts"
    backup_root = tmp_path / "backups"

    assert (
        main(
            [
                "create",
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
    create_output = capsys.readouterr().out.strip().splitlines()
    artifact_dir = Path(create_output[0].split(":", 1)[1].strip())
    assert artifact_dir.exists()

    assert main(["diff", str(artifact_dir)]) == 0
    diff_output = capsys.readouterr().out
    assert "memory" in diff_output.lower()
    assert "fact" in diff_output.lower()
    assert "confidence" in diff_output.lower()
    assert "snippet" in diff_output.lower()

    assert main(["validate", str(artifact_dir), "--live-root", str(live_root)]) == 0
    validate_output = capsys.readouterr().out
    assert "valid" in validate_output.lower()

    assert (
        main(
            [
                "apply",
                str(artifact_dir),
                "--live-root",
                str(live_root),
                "--backup-root",
                str(backup_root),
                "--approve",
                "all",
            ]
        )
        == 0
    )
    apply_output = capsys.readouterr().out
    assert "applied" in apply_output.lower()

    memory = (live_root / "memory.md").read_text(encoding="utf-8")
    assert "Keep updates short and concrete." in memory
    facts = (live_root / "facts.jsonl").read_text(encoding="utf-8").splitlines()
    assert any(json.loads(line)["key"] == "tone" for line in facts)
    skill = (live_root / "skills" / "review.md").read_text(encoding="utf-8")
    assert "Preserve review gates and backups." in skill
    assert (backup_root / "memory.md").exists()
    assert load_artifact(artifact_dir).status == "applied"

    assert main(["status", "--artifact-root", str(artifact_root)]) == 0
    status_output = capsys.readouterr().out
    assert "applied" in status_output.lower()


def test_report_card_command_redacts_private_content_and_writes_json_companion(
    tmp_path: Path, capsys
) -> None:
    artifact_dir = _write_report_card_artifact(tmp_path, status="staged")
    json_path = tmp_path / "report-card.json"

    assert main(["report-card", str(artifact_dir), "--json", str(json_path)]) == 0
    output = capsys.readouterr().out
    json_text = json_path.read_text(encoding="utf-8")
    payload = json.loads(json_text)

    assert "artifact-report-card" in output
    assert "TOP-SECRET" not in output
    assert "TOP-SECRET" not in json_text
    assert "memory updates" in output
    assert "validation state" in output.lower()
    assert payload["artifact_id"] == "artifact-report-card"
    assert payload["status"] == "staged"
    assert payload["validation_state"] == "invalid"
    assert payload["apply_state"] == "not applied"
    assert payload["discard_state"] == "not discarded"
    assert payload["target_kind_breakdown"] == {"memory": 1}
    assert payload["theme_labels"] == ["memory updates"]


def test_discard_command_archives_artifact(tmp_path: Path, capsys) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    (live_root / "memory.md").write_text("# MEMORY\n", encoding="utf-8")
    sources = _write_source_tree(tmp_path)
    artifact_root = tmp_path / "artifacts"
    archive_root = tmp_path / "archive"

    assert (
        main(
            [
                "create",
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
    artifact_dir = Path(capsys.readouterr().out.strip().splitlines()[0].split(":", 1)[1].strip())

    assert main(["discard", str(artifact_dir), "--archive-root", str(archive_root)]) == 0
    discard_output = capsys.readouterr().out
    assert "discarded" in discard_output.lower()

    assert not artifact_dir.exists()
    archived_dir = archive_root / artifact_dir.name
    assert archived_dir.exists()
    assert (live_root / "memory.md").read_text(encoding="utf-8") == "# MEMORY\n"
