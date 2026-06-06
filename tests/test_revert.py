from __future__ import annotations

from pathlib import Path

import pytest

from hermes_dreaming.artifact import DreamArtifact, DreamProposal, load_artifact, write_artifact
from hermes_dreaming.apply import (
    REVERT_FILE,
    DreamRevertError,
    apply_artifact,
    revert_artifact,
)
from hermes_dreaming.cli import main


def _write_artifact(
    tmp_path: Path,
    *,
    artifact_id: str = "artifact-revert",
    live_root: Path,
    proposals: list[DreamProposal],
    status: str = "validated",
    applied: bool = False,
    backup_paths: list[str] | None = None,
) -> Path:
    artifact = DreamArtifact(
        artifact_id=artifact_id,
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status="applied" if applied else status,
        workspace_root=str(live_root),
        source_roots=[str(tmp_path / "sources")],
        report="# Report",
        sources=[],
        proposals=proposals,
        applied_proposal_ids=[p.id for p in proposals if p.applied] if applied else [],
        backup_paths=backup_paths or [],
    )
    artifact_dir = tmp_path / artifact_id
    write_artifact(artifact, artifact_dir)
    return artifact_dir


def _memory_proposal(tmp_path: Path, *, target_path: str = "memory.md", priority: str = "normal", risk: str = "low", approved: bool = True, id_suffix: str = "") -> DreamProposal:
    return DreamProposal(
        id=f"proposal-{target_path}{id_suffix}",
        target_kind="memory",
        target_path=target_path,
        mode="append_text",
        summary="append memory note",
        provenance=["sessions/1.md:1"],
        proposed_text="- Keep updates short and concrete.",
        approved=approved,
        priority=priority,
        risk=risk,
    )


def test_apply_then_revert_roundtrip_restores_live_state(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")

    proposal = _memory_proposal(tmp_path)
    proposal.applied = True
    artifact_dir = _write_artifact(
        tmp_path,
        live_root=live_root,
        proposals=[proposal],
        applied=True,
    )
    backup_root = tmp_path / "backups"
    # Simulate the post-apply state and backup snapshot that apply_artifact would produce.
    memory.write_text("# MEMORY\n\n- Existing note\n- Keep updates short and concrete.\n", encoding="utf-8")
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / "memory.md"
    backup_path.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")
    loaded = load_artifact(artifact_dir)
    loaded.backup_paths = [str(backup_path)]
    write_artifact(loaded, artifact_dir)

    reverted = revert_artifact(artifact_dir, live_root=live_root, backup_root=backup_root, yes=True)

    assert reverted.status == "reverted"
    assert reverted.reverted_at is not None
    assert memory.read_text(encoding="utf-8") == "# MEMORY\n\n- Existing note\n"
    assert (artifact_dir / REVERT_FILE).exists()
    revert_md = (artifact_dir / REVERT_FILE).read_text(encoding="utf-8")
    assert "Restored files" in revert_md
    assert "Rolled-back proposals" in revert_md
    # Applied proposal was rolled back to approved state.
    assert reverted.proposals[0].approved is True
    assert reverted.proposals[0].applied is False
    assert any(event["action"] == "reverted" for event in reverted.revert_audit_events)


def test_revert_rejects_non_applied_artifact(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    proposal = _memory_proposal(tmp_path)
    artifact_dir = _write_artifact(
        tmp_path,
        live_root=live_root,
        proposals=[proposal],
        status="validated",
    )

    with pytest.raises(DreamRevertError, match="must be 'applied'"):
        revert_artifact(artifact_dir, live_root=live_root, backup_root=tmp_path / "backups", yes=True)


def test_revert_without_yes_prints_confirmation_and_returns_via_cli(tmp_path: Path, capsys) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")

    proposal = _memory_proposal(tmp_path)
    proposal.applied = True
    artifact_dir = _write_artifact(
        tmp_path,
        live_root=live_root,
        proposals=[proposal],
        applied=True,
    )
    backup_root = tmp_path / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / "memory.md"
    backup_path.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")
    memory.write_text("# MEMORY\n\n- Existing note\n- Keep updates short and concrete.\n", encoding="utf-8")
    loaded = load_artifact(artifact_dir)
    loaded.backup_paths = [str(backup_path)]
    write_artifact(loaded, artifact_dir)

    # CLI without --yes prints the confirmation prompt and returns exit 2.
    exit_code = main(["revert", str(artifact_dir), "--live-root", str(live_root), "--backup-root", str(backup_root)])
    assert exit_code == 2
    output = capsys.readouterr().out
    assert "Re-run with --yes to confirm" in output
    # Live file is untouched.
    assert "- Keep updates short and concrete." in memory.read_text(encoding="utf-8")


def test_revert_fails_loud_on_missing_backup_and_leaves_live_state(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")

    proposal = _memory_proposal(tmp_path)
    proposal.applied = True
    artifact_dir = _write_artifact(
        tmp_path,
        live_root=live_root,
        proposals=[proposal],
        applied=True,
        backup_paths=[str(tmp_path / "backups" / "memory.md")],
    )

    with pytest.raises(DreamRevertError, match="missing backup file"):
        revert_artifact(artifact_dir, live_root=live_root, backup_root=tmp_path / "backups", yes=True)

    # Live state is untouched.
    assert memory.read_text(encoding="utf-8") == "# MEMORY\n\n- Existing note\n"
    # Audit event recorded.
    loaded = load_artifact(artifact_dir)
    assert any(event["action"] == "revert_failed" for event in loaded.revert_audit_events)


def test_revert_records_drift_event_when_live_drifted_after_apply(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    backup_root = tmp_path / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / "memory.md"
    backup_path.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")

    # Simulate: backup has pre-apply content; live has drifted to something else
    # after the apply, before revert. Revert should still restore from backup and
    # record a drift_detected audit event.
    memory.write_text(
        "# MEMORY\n\n- Existing note\n- Keep updates short and concrete.\n- Operator edit after apply\n",
        encoding="utf-8",
    )

    proposal = _memory_proposal(tmp_path)
    proposal.applied = True
    artifact_dir = _write_artifact(
        tmp_path,
        live_root=live_root,
        proposals=[proposal],
        applied=True,
        backup_paths=[str(backup_path)],
    )

    reverted = revert_artifact(artifact_dir, live_root=live_root, backup_root=backup_root, yes=True)

    # Live state was restored from backup despite drift.
    assert memory.read_text(encoding="utf-8") == "# MEMORY\n\n- Existing note\n"
    # Drift was recorded.
    drift_events = [event for event in reverted.revert_audit_events if event["action"] == "drift_detected"]
    assert drift_events
    assert any("memory.md" in event.get("target", "") for event in drift_events)


def test_revert_writes_manifest_audit_and_revert_md(tmp_path: Path) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")

    proposal = _memory_proposal(tmp_path)
    proposal.applied = True
    artifact_dir = _write_artifact(
        tmp_path,
        live_root=live_root,
        proposals=[proposal],
        applied=True,
    )
    backup_root = tmp_path / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / "memory.md"
    backup_path.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")
    memory.write_text("# MEMORY\n\n- Existing note\n- Keep updates short and concrete.\n", encoding="utf-8")
    loaded = load_artifact(artifact_dir)
    loaded.backup_paths = [str(backup_path)]
    write_artifact(loaded, artifact_dir)

    revert_artifact(artifact_dir, live_root=live_root, backup_root=backup_root, yes=True)

    # Manifest updated to reverted + reverted_at
    manifest = load_artifact(artifact_dir)
    assert manifest.status == "reverted"
    assert manifest.reverted_at is not None
    # Revert events are persisted in manifest.revert_audit_events.
    assert any(event["action"] == "reverted" for event in manifest.revert_audit_events)
    # REVERT.md present
    assert (artifact_dir / REVERT_FILE).exists()


def test_cli_revert_end_to_end_with_yes(tmp_path: Path, capsys) -> None:
    live_root = tmp_path / "live"
    live_root.mkdir()
    memory = live_root / "memory.md"
    memory.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")

    proposal = _memory_proposal(tmp_path)
    proposal.applied = True
    artifact_dir = _write_artifact(
        tmp_path,
        live_root=live_root,
        proposals=[proposal],
        applied=True,
    )
    backup_root = tmp_path / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / "memory.md"
    backup_path.write_text("# MEMORY\n\n- Existing note\n", encoding="utf-8")
    memory.write_text("# MEMORY\n\n- Existing note\n- Keep updates short and concrete.\n", encoding="utf-8")
    loaded = load_artifact(artifact_dir)
    loaded.backup_paths = [str(backup_path)]
    write_artifact(loaded, artifact_dir)

    exit_code = main(
        [
            "revert",
            str(artifact_dir),
            "--live-root",
            str(live_root),
            "--backup-root",
            str(backup_root),
            "--yes",
        ]
    )
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "reverted artifact" in output
    assert memory.read_text(encoding="utf-8") == "# MEMORY\n\n- Existing note\n"
