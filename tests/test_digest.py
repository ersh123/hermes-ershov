from __future__ import annotations

from pathlib import Path
import shlex

from hermes_dreaming.artifact import DreamArtifact, DreamProposal, write_artifact
from hermes_dreaming.cli import main
from hermes_dreaming.state import record_run


def _make_artifact(
    root: Path,
    *,
    artifact_id: str,
    created_at: str,
    status: str,
    workspace_root: Path,
    proposals: list[DreamProposal],
    audit_events: list[dict[str, object]] | None = None,
    backup_paths: list[str] | None = None,
    backup_records: list[dict[str, object]] | None = None,
) -> Path:
    artifact = DreamArtifact(
        artifact_id=artifact_id,
        created_at=created_at,
        provider="offline-marker",
        status=status,
        workspace_root=str(workspace_root),
        source_roots=[str(root / "sources")],
        report="# Report\n",
        sources=[],
        proposals=proposals,
        audit_events=audit_events or [],
        applied_proposal_ids=[proposal.id for proposal in proposals if proposal.applied],
        backup_paths=backup_paths or [],
        backup_records=backup_records or [],
        applied_at=created_at if status == "applied" else None,
        discarded_at=created_at if status == "discarded" else None,
    )
    artifact_dir = root / artifact_id
    write_artifact(artifact, artifact_dir)
    return artifact_dir


def _proposal(
    proposal_id: str,
    *,
    target_kind: str,
    target_path: str,
    summary: str,
    confidence: float,
    approved: bool = False,
    rejected: bool = False,
    rejection_reason: str | None = None,
    applied: bool = False,
    provenance: list[str] | None = None,
    proposed_text: str = "- Example text",
    risk: str = "low",
    priority: str = "normal",
    reason: str = "",
    source_quote: str = "",
    policy_flags: list[str] | None = None,
) -> DreamProposal:
    return DreamProposal(
        id=proposal_id,
        target_kind=target_kind,
        target_path=target_path,
        mode="append_text",
        summary=summary,
        provenance=provenance or ["sessions/example.md:1"],
        proposed_text=proposed_text,
        approved=approved,
        confidence=confidence,
        risk=risk,
        priority=priority,
        reason=reason,
        source_quote=source_quote,
        policy_flags=policy_flags or [],
        rejected=rejected,
        rejection_reason=rejection_reason,
        applied=applied,
    )


def test_digest_renders_local_priorities_deltas_and_weekly_rollup(tmp_path: Path, capsys) -> None:
    artifact_root = tmp_path / "artifacts"
    state_root = tmp_path / "state"
    artifact_root.mkdir()
    state_root.mkdir()

    workspace_root = tmp_path / "live"
    workspace_root.mkdir()

    previous_dir = _make_artifact(
        artifact_root,
        artifact_id="artifact-previous",
        created_at="2026-05-26T12:00:00Z",
        status="staged",
        workspace_root=workspace_root,
        proposals=[
            _proposal(
                "p-user",
                target_kind="user",
                target_path="user.md",
                summary="tighten digest intro",
                confidence=0.80,
                approved=True,
            ),
            _proposal(
                "p-fact",
                target_kind="fact",
                target_path="facts.jsonl",
                summary="track weekly watchlist",
                confidence=0.76,
                approved=False,
            ),
        ],
        audit_events=[
            {
                "timestamp": "2026-05-26T12:30:00Z",
                "artifact_id": "artifact-previous",
                "action": "approved",
                "proposal_id": "p-user",
                "target_kind": "user",
                "target_path": "user.md",
                "from_state": "pending",
                "to_state": "approved",
            },
            {
                "timestamp": "2026-05-26T12:45:00Z",
                "artifact_id": "artifact-previous",
                "action": "rejected",
                "proposal_id": "p-fact",
                "target_kind": "fact",
                "target_path": "facts.jsonl",
                "from_state": "pending",
                "to_state": "rejected",
                "reason": "too broad",
            },
        ],
    )

    current_dir = _make_artifact(
        artifact_root,
        artifact_id="artifact-current",
        created_at="2026-05-27T12:00:00Z",
        status="staged",
        workspace_root=workspace_root,
        proposals=[
            _proposal(
                "p-user",
                target_kind="user",
                target_path="user.md",
                summary="tighten digest intro",
                confidence=0.93,
                approved=True,
            ),
            _proposal(
                "p-skill",
                target_kind="skill",
                target_path="skills/digest.md",
                summary="capture digest generator workflow",
                confidence=0.89,
                approved=False,
            ),
            _proposal(
                "p-memory",
                target_kind="memory",
                target_path="memory.md",
                summary="add weekly rollup watchlist",
                confidence=0.61,
                rejected=True,
                rejection_reason="too broad",
            ),
        ],
        audit_events=[
            {
                "timestamp": "2026-05-27T12:30:00Z",
                "artifact_id": "artifact-current",
                "action": "approved",
                "proposal_id": "p-user",
                "target_kind": "user",
                "target_path": "user.md",
                "from_state": "pending",
                "to_state": "approved",
            },
            {
                "timestamp": "2026-05-27T12:45:00Z",
                "artifact_id": "artifact-current",
                "action": "rejected",
                "proposal_id": "p-memory",
                "target_kind": "memory",
                "target_path": "memory.md",
                "from_state": "pending",
                "to_state": "rejected",
                "reason": "too broad",
            },
        ],
    )

    state_path = state_root / "state.json"
    ledger_path = state_root / "runs.jsonl"
    diary_path = state_root / "ERSHOV.md"
    record_run(
        {
            "command": "create",
            "success": True,
            "timestamp": "2026-05-26T12:00:00Z",
            "summary": "staged artifact-previous",
            "artifact_id": "artifact-previous",
            "artifact_status": "staged",
            "artifact_dir": str(previous_dir),
        },
        state_path=state_path,
        ledger_path=ledger_path,
        diary_path=diary_path,
    )
    record_run(
        {
            "command": "create",
            "success": True,
            "timestamp": "2026-05-27T12:00:00Z",
            "summary": "staged artifact-current",
            "artifact_id": "artifact-current",
            "artifact_status": "staged",
            "artifact_dir": str(current_dir),
        },
        state_path=state_path,
        ledger_path=ledger_path,
        diary_path=diary_path,
    )

    assert (
        main(
            [
                "digest",
                str(current_dir),
                "--artifact-root",
                str(artifact_root),
                "--state-root",
                str(state_root),
                "--weekly",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out

    assert "Hermes Ershov digest" in output
    assert "Priority:" in output
    assert "Previous successful memory run: `artifact-previous`" in output
    assert "Next step: approve or reject proposals" in output
    assert f"ershov approve {shlex.quote(str(current_dir))} p-user" in output
    assert f"ershov reject {shlex.quote(str(current_dir))} p-memory --reason \"...\"" in output
    assert "What changed since last memory run" in output
    assert "Changed:" in output
    assert "Repeated:" in output
    assert "Weekly rollup" in output
    assert "Accepted themes:" in output
    assert "Rejected themes:" in output
    assert "Recurring themes:" in output
    assert "Next-week watchlist:" in output
    assert "no Telegram send by default" in output


def test_digest_separates_backup_copies_from_rollback_evidence(tmp_path: Path, capsys) -> None:
    artifact_root = tmp_path / "artifacts"
    state_root = tmp_path / "state"
    artifact_root.mkdir()
    state_root.mkdir()

    workspace_root = tmp_path / "live"
    workspace_root.mkdir()

    current_dir = _make_artifact(
        artifact_root,
        artifact_id="artifact-created-file",
        created_at="2026-05-27T12:00:00Z",
        status="applied",
        workspace_root=workspace_root,
        proposals=[
            _proposal(
                "p-skill",
                target_kind="skill",
                target_path="skills/new.md",
                summary="create new skill note",
                confidence=0.91,
                approved=True,
                applied=True,
            )
        ],
        backup_records=[
            {
                "proposal_id": "p-skill",
                "target_relative": "skills/new.md",
                "existed_before": False,
            }
        ],
    )

    assert (
        main(
            [
                "digest",
                str(current_dir),
                "--artifact-root",
                str(artifact_root),
                "--state-root",
                str(state_root),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out

    assert "- Backup file copies: `0`" in output
    assert "- Rollback evidence records: `1`" in output
    assert "- Created-file tombstones: `1`" in output
    assert "Backup copies:" not in output


def test_digest_inbox_mode_renders_attention_blocks_and_counts(tmp_path: Path, capsys) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()

    shared_workspace = tmp_path / "live"
    shared_workspace.mkdir()

    _make_artifact(
        artifact_root,
        artifact_id="artifact-older",
        created_at="2026-05-26T12:00:00Z",
        status="staged",
        workspace_root=shared_workspace,
        proposals=[
            _proposal(
                "p-safe",
                target_kind="memory",
                target_path="memory.md",
                summary="safe proposal",
                confidence=0.61,
                approved=True,
                risk="low",
                priority="normal",
                reason="routine note",
                source_quote="safe quote",
            )
        ],
    )
    _make_artifact(
        artifact_root,
        artifact_id="artifact-newer",
        created_at="2026-05-27T12:00:00Z",
        status="staged",
        workspace_root=shared_workspace,
        proposals=[
            _proposal(
                "p-high",
                target_kind="skill",
                target_path="skills/digest.md",
                summary="high-priority fix",
                confidence=0.92,
                approved=True,
                risk="high",
                priority="high",
                reason="needs operator now",
                source_quote="this is the line operator needs",
                policy_flags=["manual-review"],
            ),
            _proposal(
                "p-pending",
                target_kind="fact",
                target_path="facts.jsonl",
                summary="follow-up note",
                confidence=0.55,
                approved=False,
                risk="low",
                priority="normal",
                reason="follow up later",
                source_quote="pending quote",
            ),
        ],
    )

    assert (
        main([
            "digest",
            "--inbox",
            "--artifact-root",
            str(artifact_root),
            "--limit",
            "10",
        ])
        == 0
    )
    output = capsys.readouterr().out

    assert "Hermes Ershov inbox digest" in output
    assert "- Total artifacts: `2`" in output
    assert "- Active artifacts: `2`" in output
    assert "- High risk count: `1`" in output
    assert "- High priority count: `1`" in output
    assert "- Newest artifact: `artifact-newer`" in output
    assert "- Top reason: needs operator now" in output
    assert "## Needs Operator" in output
    assert "artifact-newer" in output
    assert "manual-review" in output
    assert "## Safe to ignore" in output
    assert "artifact-older" in output
    assert "Delivery: local only, no Telegram send by default." in output
