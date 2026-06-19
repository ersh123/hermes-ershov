from __future__ import annotations

from pathlib import Path
import shlex

import pytest

from hermes_dreaming.artifact import DreamArtifact, DreamProposal, load_artifact, write_artifact
from hermes_dreaming.cli import main


def _artifact(tmp_path: Path) -> tuple[Path, Path]:
    live_root = tmp_path / "live"
    live_root.mkdir()
    artifact = DreamArtifact(
        artifact_id="artifact-review",
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status="staged",
        workspace_root=str(live_root),
        source_roots=[str(live_root / "sources")],
        report="# Report\n\nReview workflow fixture.",
        sources=[],
        proposals=[
            DreamProposal(
                id="proposal-memory",
                target_kind="memory",
                target_path="memory.md",
                mode="append_text",
                summary="append memory note",
                provenance=["sessions/1.md:1"],
                proposed_text="- Keep updates short and concrete.",
                approved=False,
            ),
            DreamProposal(
                id="proposal-user",
                target_kind="user",
                target_path="user.md",
                mode="append_text",
                summary="append user note",
                provenance=["sessions/1.md:2"],
                proposed_text="- Prefer concise status updates.",
                approved=False,
            ),
        ],
    )
    artifact_dir = tmp_path / "artifact"
    write_artifact(artifact, artifact_dir)
    return live_root, artifact_dir


def test_approve_reject_summarize_and_open_command_flow(tmp_path: Path, capsys) -> None:
    live_root, artifact_dir = _artifact(tmp_path)

    assert main(["approve", str(artifact_dir), "proposal-memory"]) == 0
    approve_output = capsys.readouterr().out
    assert "approved artifact: artifact-review (1 changed)" in approve_output

    loaded = load_artifact(artifact_dir)
    assert loaded.proposals[0].approved is True
    assert loaded.proposals[0].rejected is False
    assert loaded.audit_events[-1]["action"] == "approved"

    assert main(["reject", str(artifact_dir), "proposal-user", "--reason", "too broad"]) == 0
    reject_output = capsys.readouterr().out
    assert "rejected artifact: artifact-review (1 changed)" in reject_output

    loaded = load_artifact(artifact_dir)
    assert loaded.proposals[1].approved is False
    assert loaded.proposals[1].rejected is True
    assert loaded.proposals[1].rejection_reason == "too broad"
    assert loaded.audit_events[-1]["action"] == "rejected"
    audit_lines = (artifact_dir / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 2

    assert main(["summarize", str(artifact_dir)]) == 0
    summary_output = capsys.readouterr().out
    assert "State counts: pending=0, approved=1, rejected=1, applied=0" in summary_output
    assert "Recent audit" in summary_output
    assert "too broad" in summary_output

    assert main(["review", "--open", str(artifact_dir)]) == 0
    open_output = capsys.readouterr().out
    assert f"Artifact: `{artifact_dir}`" in open_output
    assert "mnemos approve" in open_output
    assert "mnemos reject" in open_output
    assert "mnemos validate" in open_output

    assert main(["approve", str(artifact_dir), "proposal-memory"]) == 0
    repeat_approve_output = capsys.readouterr().out
    assert "no changes" in repeat_approve_output
    assert len(load_artifact(artifact_dir).audit_events) == 2

    assert main(["reject", str(artifact_dir), "proposal-user", "--reason", "too broad"]) == 0
    repeat_reject_output = capsys.readouterr().out
    assert "no changes" in repeat_reject_output
    assert len(load_artifact(artifact_dir).audit_events) == 2

    assert main(["approve", str(artifact_dir), "missing-proposal"]) == 1
    invalid_output = capsys.readouterr().out
    assert "unknown proposal id" in invalid_output

    assert main(["reject", str(artifact_dir), "missing-proposal", "--reason", "nope"]) == 1
    invalid_reject_output = capsys.readouterr().out
    assert "unknown proposal id" in invalid_reject_output
    assert live_root.exists()


def test_summarize_uses_quoted_live_root_examples_for_spaced_paths(tmp_path: Path, capsys) -> None:
    live_root = tmp_path / "live root"
    live_root.mkdir()
    artifact = DreamArtifact(
        artifact_id="artifact-quoted",
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status="staged",
        workspace_root=str(live_root),
        source_roots=[str(live_root / "sources")],
        report="# Report\n\nQuoted path fixture.",
        sources=[],
        proposals=[
            DreamProposal(
                id="proposal-memory",
                target_kind="memory",
                target_path="memory.md",
                mode="append_text",
                summary="append memory note",
                provenance=["sessions/1.md:1"],
                proposed_text="- Keep updates short and concrete.",
                approved=False,
            )
        ],
    )
    artifact_dir = tmp_path / "artifact quoted"
    write_artifact(artifact, artifact_dir)

    assert main(["summarize", str(artifact_dir)]) == 0
    summary_output = capsys.readouterr().out
    quoted_live_root = shlex.quote(str(live_root))
    assert f"--live-root {quoted_live_root}" in summary_output
    assert f"mnemos apply {shlex.quote(str(artifact_dir))} --live-root {quoted_live_root}" in summary_output


def test_reject_artifact_enforces_non_empty_reason_at_command_layer(tmp_path: Path) -> None:
    from hermes_dreaming.artifact import load_artifact
    from hermes_dreaming.commands.review import ReviewError, reject_artifact

    live_root = tmp_path / "live"
    live_root.mkdir()
    artifact = DreamArtifact(
        artifact_id="artifact-reject-enforce",
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status="staged",
        workspace_root=str(live_root),
        source_roots=[str(live_root / "sources")],
        report="# Report",
        sources=[],
        proposals=[
            DreamProposal(
                id="proposal-memory",
                target_kind="memory",
                target_path="memory.md",
                mode="append_text",
                summary="append memory note",
                provenance=["sessions/1.md:1"],
                proposed_text="- Keep updates short and concrete.",
                approved=False,
            )
        ],
    )
    artifact_dir = tmp_path / "artifact-reject-enforce"
    write_artifact(artifact, artifact_dir)

    # Missing reason at command layer raises ReviewError.
    with pytest.raises(ReviewError, match="non-empty reason"):
        reject_artifact(artifact_dir, "proposal-memory", reason=None)
    # Empty reason raises the same.
    with pytest.raises(ReviewError, match="non-empty reason"):
        reject_artifact(artifact_dir, "proposal-memory", reason="")
    # Whitespace-only reason raises the same.
    with pytest.raises(ReviewError, match="non-empty reason"):
        reject_artifact(artifact_dir, "proposal-memory", reason="   \n  ")

    # No audit event was recorded for the failed attempts.
    loaded = load_artifact(artifact_dir)
    assert not any(event["action"] == "rejected" for event in loaded.audit_events)

    # A non-empty reason succeeds and records the audit event with reason.
    result = reject_artifact(artifact_dir, "proposal-memory", reason="too broad for v1")
    assert result.changed == 1
    loaded = load_artifact(artifact_dir)
    reject_events = [event for event in loaded.audit_events if event["action"] == "rejected"]
    assert len(reject_events) == 1
    assert reject_events[0].get("reason") == "too broad for v1"


def test_reject_command_cli_returns_error_on_missing_reason(tmp_path: Path, capsys) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    artifact = DreamArtifact(
        artifact_id="artifact-cli-reject-enforce",
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status="staged",
        workspace_root=str(live_root),
        source_roots=[str(live_root / "sources")],
        report="# Report",
        sources=[],
        proposals=[
            DreamProposal(
                id="proposal-memory",
                target_kind="memory",
                target_path="memory.md",
                mode="append_text",
                summary="append memory note",
                provenance=["sessions/1.md:1"],
                proposed_text="- Keep updates short and concrete.",
                approved=False,
            )
        ],
    )
    artifact_dir = tmp_path / "artifact-cli-reject-enforce"
    write_artifact(artifact, artifact_dir)

    exit_code = main(["reject", str(artifact_dir), "proposal-memory"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "non-empty reason" in output.lower()
