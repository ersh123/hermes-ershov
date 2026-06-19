from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import shlex

from ..analyze import DreamCreationResult, DreamRunConfig, create_dream_artifact
from ..artifact import DreamArtifact, DreamArtifactStateError, DreamProposal, load_artifact, proposal_state, record_proposal_transition, write_artifact
from ..triage import proposal_detail_lines, sorted_proposals


class ReviewError(RuntimeError):
    pass


@dataclass(slots=True)
class ReviewMutationResult:
    artifact: DreamArtifact
    changed: int
    unchanged: int


def handle(config: DreamRunConfig) -> DreamCreationResult:
    """Create and validate a staged artifact without applying it."""

    return create_dream_artifact(config)


def _count_states(proposals: list[DreamProposal]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for proposal in proposals:
        counts[proposal_state(proposal)] += 1
    return counts


def _resolve_targets(artifact: DreamArtifact, proposal_ref: str) -> list[DreamProposal]:
    normalized = proposal_ref.strip().lower()
    if normalized in {"all", "*"}:
        return list(artifact.proposals)
    for proposal in artifact.proposals:
        if proposal.id == proposal_ref:
            return [proposal]
    raise ReviewError(f"unknown proposal id: {proposal_ref}")


def _mutate_review_state(
    artifact_dir: Path,
    *,
    proposal_ref: str,
    to_state: str,
    reason: str | None = None,
) -> ReviewMutationResult:
    artifact = load_artifact(artifact_dir)
    targets = _resolve_targets(artifact, proposal_ref)
    changed = 0
    unchanged = 0

    try:
        for proposal in targets:
            changed_this = record_proposal_transition(
                artifact,
                proposal,
                to_state=to_state,
                reason=reason,
                command=to_state,
            )
            if changed_this:
                changed += 1
            else:
                unchanged += 1
    except DreamArtifactStateError as exc:
        raise ReviewError(str(exc)) from exc

    if changed:
        write_artifact(artifact, artifact_dir)

    return ReviewMutationResult(artifact=artifact, changed=changed, unchanged=unchanged)


def approve_artifact(artifact_dir: Path, proposal_ref: str) -> ReviewMutationResult:
    return _mutate_review_state(artifact_dir, proposal_ref=proposal_ref, to_state="approved")


def reject_artifact(artifact_dir: Path, proposal_ref: str, *, reason: str | None) -> ReviewMutationResult:
    if reason is None or not reason.strip():
        raise ReviewError("A non-empty reason is required to reject an artifact")
    return _mutate_review_state(artifact_dir, proposal_ref=proposal_ref, to_state="rejected", reason=reason.strip())


def render_open_brief(artifact_dir: Path) -> str:
    artifact = load_artifact(artifact_dir)
    live_root = Path(artifact.workspace_root)
    live_root_text = shlex.quote(str(live_root))
    artifact_text = shlex.quote(str(artifact_dir))
    lines = [
        "# Hermes Ershov review",
        "",
        f"Artifact: `{artifact_text}`",
        f"Artifact id: `{artifact.artifact_id}`",
        f"Status: `{artifact.status}`",
        f"Live root: `{live_root_text}`",
        "",
        "## Next commands",
        "",
        f"- `ershov summarize {artifact_text}`",
        f"- `ershov approve {artifact_text} all`",
        f"- `ershov reject {artifact_text} <proposal-id> --reason \"...\"`",
        f"- `ershov diff {artifact_text} --live-root {live_root_text}`",
        f"- `ershov validate {artifact_text} --live-root {live_root_text}`",
        f"- `ershov apply {artifact_text} --live-root {live_root_text} --backup-root <backup-root>`",
    ]
    return "\n".join(lines) + "\n"


def render_summary(artifact_dir: Path) -> str:
    artifact = load_artifact(artifact_dir)
    counts = _count_states(artifact.proposals)
    artifact_text = shlex.quote(str(artifact_dir))
    live_root_text = shlex.quote(str(Path(artifact.workspace_root)))
    lines = [
        "# Hermes Ershov summary",
        "",
        f"Artifact: `{artifact_text}`",
        f"Artifact id: `{artifact.artifact_id}`",
        f"Status: `{artifact.status}`",
        f"Proposals: `{len(artifact.proposals)}`",
        f"State counts: pending={counts.get('pending', 0)}, approved={counts.get('approved', 0)}, rejected={counts.get('rejected', 0)}, applied={counts.get('applied', 0)}",
        "",
        "## Decisions",
        "",
    ]
    if artifact.proposals:
        for proposal in sorted_proposals(artifact.proposals):
            lines.extend(proposal_detail_lines(proposal))
    else:
        lines.append("- None")

    if artifact.audit_events:
        lines.extend(["", "## Recent audit", ""])
        for event in artifact.audit_events[-5:]:
            line = (
                f"- {event.get('timestamp', 'unknown time')} {event.get('action', 'event')} "
                f"{event.get('proposal_id', 'unknown')} {event.get('from_state', '?')}→{event.get('to_state', '?')}"
            )
            reason = event.get('reason')
            if reason:
                line += f", reason: {reason}"
            lines.append(line)

    lines.extend(
        [
            "",
            "## Next commands",
            "",
            f"- `ershov review --open {artifact_text}`",
            f"- `ershov approve {artifact_text} all`",
            f"- `ershov reject {artifact_text} <proposal-id> --reason \"...\"`",
            f"- `ershov diff {artifact_text} --live-root {live_root_text}`",
            f"- `ershov validate {artifact_text} --live-root {live_root_text}`",
            f"- `ershov apply {artifact_text} --live-root {live_root_text} --backup-root <backup-root>`",
        ]
    )
    return "\n".join(lines) + "\n"
