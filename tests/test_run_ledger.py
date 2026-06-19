from __future__ import annotations

import json
from pathlib import Path

from hermes_dreaming.artifact import DreamArtifact, DreamProposal, SourceSnapshot, write_artifact
from hermes_dreaming.cli import main
from hermes_dreaming.state import read_run_ledger, record_run


def _artifact(tmp_path: Path, *, artifact_id: str, status: str) -> Path:
    artifact = DreamArtifact(
        artifact_id=artifact_id,
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status=status,
        workspace_root=str(tmp_path),
        source_roots=[str(tmp_path / "sources")],
        report="# Report",
        sources=[
            SourceSnapshot(
                path="sessions/2026-05-25.md",
                kind="session",
                content="MEMORY: memory: Keep updates short and concrete.\n",
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
                provenance=["sessions/2026-05-25.md:1"],
                proposed_text="- Keep updates short and concrete.",
                approved=True,
            )
        ],
    )
    artifact_dir = tmp_path / artifact_id
    write_artifact(artifact, artifact_dir)
    return artifact_dir


def test_record_run_appends_ledger_and_rewrites_dreams_md(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    ledger_path = tmp_path / "runs.jsonl"
    diary_path = tmp_path / "MNEMOS.md"

    first = record_run(
        {
            "command": "create",
            "success": False,
            "timestamp": "2026-05-25T12:00:00Z",
            "summary": "validation failed",
            "artifact_id": "dream-1",
            "artifact_status": "invalid",
        },
        state_path=state_path,
        ledger_path=ledger_path,
        diary_path=diary_path,
    )
    second = record_run(
        {
            "command": "apply",
            "success": True,
            "timestamp": "2026-05-25T13:00:00Z",
            "summary": "applied cleanly",
            "artifact_id": "dream-2",
            "artifact_status": "applied",
        },
        state_path=state_path,
        ledger_path=ledger_path,
        diary_path=diary_path,
    )

    assert read_run_ledger(ledger_path=ledger_path) == [first, second]

    diary = diary_path.read_text(encoding="utf-8")
    assert diary.startswith("# MNEMOS.md")
    assert "2026-05-25T12:00:00Z" in diary
    assert "create" in diary
    assert "validation failed" in diary
    assert "2026-05-25T13:00:00Z" in diary
    assert "apply" in diary
    assert "applied cleanly" in diary

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["last_run"]["command"] == "apply"
    assert state["last_successful_run"]["command"] == "apply"
    assert state["run_count"] == 2
    assert state["successful_run_count"] == 1


def test_status_command_reports_last_run_success_and_artifact_state(tmp_path: Path, monkeypatch, capsys) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    (live_root / "memory.md").write_text("# MEMORY\n", encoding="utf-8")

    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    _artifact(artifact_root, artifact_id="artifact-staged", status="staged")
    _artifact(artifact_root, artifact_id="artifact-applied", status="applied")

    state_path = tmp_path / "state.json"
    ledger_path = tmp_path / "runs.jsonl"
    diary_path = tmp_path / "MNEMOS.md"

    record_run(
        {
            "command": "create",
            "success": False,
            "timestamp": "2026-05-25T12:00:00Z",
            "summary": "validation failed",
            "artifact_id": "artifact-staged",
            "artifact_status": "invalid",
        },
        state_path=state_path,
        ledger_path=ledger_path,
        diary_path=diary_path,
    )
    record_run(
        {
            "command": "apply",
            "success": True,
            "timestamp": "2026-05-25T13:00:00Z",
            "summary": "applied cleanly",
            "artifact_id": "artifact-applied",
            "artifact_status": "applied",
        },
        state_path=state_path,
        ledger_path=ledger_path,
        diary_path=diary_path,
    )

    monkeypatch.setattr("hermes_dreaming.state.STATE_JSON", state_path)
    monkeypatch.setattr("hermes_dreaming.state.RUN_LEDGER_JSONL", ledger_path)
    monkeypatch.setattr("hermes_dreaming.state.DREAMS_MD_PATH", diary_path)

    assert main(["status", "--artifact-root", str(artifact_root)]) == 0
    output = capsys.readouterr().out

    assert "Last run:" in output
    assert "apply" in output
    assert "Last successful run:" in output
    assert "artifact-applied" in output
    assert "Artifact state:" in output
    assert "staged=1" in output or "staged: 1" in output
    assert "applied=1" in output or "applied: 1" in output
    assert "Memory usage:" in output
    assert "MNEMOS.md" in output
