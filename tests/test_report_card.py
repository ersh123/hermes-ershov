from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest

from hermes_dreaming.analyze import render_report_card_json, render_report_card_markdown
from hermes_dreaming.artifact import DreamArtifact, DreamProposal, SourceSnapshot, write_artifact
from hermes_dreaming.commands.report_card import handle as report_card_handle


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
                content="MEMORY: memory: TOP-SECRET-SOURCE\n",
                sha256=sha256(b"MEMORY: memory: TOP-SECRET-SOURCE\n").hexdigest(),
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


def test_report_card_redacts_private_content_and_renders_json(tmp_path: Path) -> None:
    artifact_dir = _write_report_card_artifact(tmp_path, status="staged")
    report_card = report_card_handle(artifact_dir)

    markdown = render_report_card_markdown(report_card)
    json_text = render_report_card_json(report_card)
    payload = json.loads(json_text)

    assert report_card.artifact_id == "artifact-report-card"
    assert report_card.validation_state == "invalid"
    assert report_card.apply_state == "not applied"
    assert report_card.discard_state == "not discarded"
    assert report_card.target_kind_breakdown == {"memory": 1}
    assert report_card.theme_labels == ["memory updates"]
    assert "TOP-SECRET" not in markdown
    assert "TOP-SECRET" not in json_text
    assert payload["artifact_id"] == "artifact-report-card"
    assert payload["source_count"] == 1
    assert payload["proposal_count"] == 1
    assert payload["validation_error_count"] == 1
    assert payload["target_kind_breakdown"] == {"memory": 1}


def test_report_card_separates_backup_copies_from_rollback_evidence(tmp_path: Path) -> None:
    artifact = DreamArtifact(
        artifact_id="artifact-created-file",
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status="applied",
        workspace_root=str(tmp_path),
        source_roots=[str(tmp_path / "sources")],
        report="# report\n",
        sources=[],
        proposals=[],
        validation_errors=[],
        applied_at="2026-05-25T13:00:00Z",
        backup_records=[
            {
                "proposal_id": "proposal-skill",
                "target_relative": "skills/new.md",
                "existed_before": False,
            }
        ],
    )
    artifact_dir = tmp_path / artifact.artifact_id
    write_artifact(artifact, artifact_dir)

    report_card = report_card_handle(artifact_dir)
    markdown = render_report_card_markdown(report_card)
    payload = json.loads(render_report_card_json(report_card))

    assert report_card.backup_count == 0
    assert report_card.rollback_evidence_count == 1
    assert report_card.created_file_tombstone_count == 1
    assert "- Backup file copies: `0`" in markdown
    assert "- Rollback evidence records: `1`" in markdown
    assert "- Created-file tombstones: `1`" in markdown
    assert "Backup copies:" not in markdown
    assert payload["backup_count"] == 0
    assert payload["rollback_evidence_count"] == 1
    assert payload["created_file_tombstone_count"] == 1


@pytest.mark.parametrize(
    ("status", "applied_at", "discarded_at", "expected_apply_state", "expected_discard_state"),
    [
        ("applied", "2026-05-25T13:00:00Z", None, "applied", "not discarded"),
        ("discarded", None, "2026-05-25T14:00:00Z", "not applied", "discarded"),
    ],
)
def test_report_card_reflects_applied_and_discarded_states(
    tmp_path: Path,
    status: str,
    applied_at: str | None,
    discarded_at: str | None,
    expected_apply_state: str,
    expected_discard_state: str,
) -> None:
    artifact = DreamArtifact(
        artifact_id=f"artifact-{status}",
        created_at="2026-05-25T12:00:00Z",
        provider="offline-marker",
        status=status,
        workspace_root=str(tmp_path),
        source_roots=[str(tmp_path / "sources")],
        report="# report\n",
        sources=[],
        proposals=[],
        validation_errors=[],
        applied_at=applied_at,
        discarded_at=discarded_at,
    )
    artifact_dir = tmp_path / artifact.artifact_id
    write_artifact(artifact, artifact_dir)

    report_card = report_card_handle(artifact_dir)

    assert report_card.status == status
    assert report_card.apply_state == expected_apply_state
    assert report_card.discard_state == expected_discard_state
    assert report_card.theme_labels == []
    assert report_card.target_kind_breakdown == {}
