from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .artifact import DreamProposal, proposal_state

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
PRIORITY_ORDER = {"low": 0, "normal": 1, "high": 2}
STATE_ORDER = {"pending": 0, "approved": 1, "rejected": 2, "applied": 3}


@dataclass(slots=True)
class ProposalView:
    id: str
    state: str
    target_kind: str
    target_path: str
    summary: str
    confidence: float
    risk: str
    priority: str
    reason: str
    source_quote: str
    policy_flags: list[str]
    provenance: list[str]


def normalize_level(value: str | None, *, default: str, order: dict[str, int]) -> str:
    normalized = str(value or default).strip().lower()
    if normalized not in order:
        return default
    return normalized


def risk_rank(value: str | None) -> int:
    return RISK_ORDER.get(normalize_level(value, default="low", order=RISK_ORDER), 0)


def priority_rank(value: str | None) -> int:
    return PRIORITY_ORDER.get(normalize_level(value, default="normal", order=PRIORITY_ORDER), 0)


def highest_level(values: Iterable[DreamProposal], attr: str, *, order: dict[str, int], default: str) -> str:
    best = default
    best_rank = order.get(default, 0)
    for proposal in values:
        value = normalize_level(getattr(proposal, attr, default), default=default, order=order)
        rank = order.get(value, -1)
        if rank > best_rank:
            best = value
            best_rank = rank
    return best


def sorted_proposals(proposals: Iterable[DreamProposal]) -> list[DreamProposal]:
    def _key(proposal: DreamProposal) -> tuple[int, int, int, float, str]:
        return (
            -priority_rank(getattr(proposal, "priority", None)),
            -risk_rank(getattr(proposal, "risk", None)),
            STATE_ORDER.get(proposal_state(proposal), 0),
            -float(getattr(proposal, "confidence", 0.0) or 0.0),
            proposal.id,
        )

    return sorted(proposals, key=_key)


def sort_priority_rows(rows: Iterable[object], *, priority_attr: str = "highest_priority", risk_attr: str = "highest_risk", created_at_attr: str = "created_at") -> list[object]:
    def _key(row: object) -> tuple[int, int, str]:
        priority = getattr(row, priority_attr, "normal")
        risk = getattr(row, risk_attr, "low")
        created_at = str(getattr(row, created_at_attr, ""))
        return (-priority_rank(priority), -risk_rank(risk), created_at)

    return sorted(rows, key=_key)


def aggregate_policy_flags(proposals: Iterable[DreamProposal]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for proposal in proposals:
        for flag in proposal.policy_flags:
            normalized = str(flag).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def proposal_view(proposal: DreamProposal) -> ProposalView:
    return ProposalView(
        id=proposal.id,
        state=proposal_state(proposal),
        target_kind=proposal.target_kind,
        target_path=proposal.target_path,
        summary=proposal.summary,
        confidence=proposal.confidence,
        risk=normalize_level(proposal.risk, default="low", order=RISK_ORDER),
        priority=normalize_level(proposal.priority, default="normal", order=PRIORITY_ORDER),
        reason=str(proposal.reason or "").strip(),
        source_quote=str(proposal.source_quote or proposal.snippet or "").strip(),
        policy_flags=[str(flag).strip() for flag in proposal.policy_flags if str(flag).strip()],
        provenance=[str(item).strip() for item in proposal.provenance if str(item).strip()],
    )


def proposal_detail_lines(proposal: DreamProposal, *, indent: str = "  - ") -> list[str]:
    view = proposal_view(proposal)
    lines = [
        f"{indent}`{view.id}` [{view.state}] `{view.target_kind}` -> `{view.target_path}`",
        f"{indent}summary: {view.summary}",
        f"{indent}risk/priority: `{view.risk}` / `{view.priority}`",
        f"{indent}confidence: `{view.confidence:.2f}`",
    ]
    if view.reason:
        lines.append(f"{indent}reason: {view.reason}")
    if view.source_quote:
        lines.append(f"{indent}source quote: {view.source_quote}")
    if view.policy_flags:
        lines.append(f"{indent}policy flags: {', '.join(view.policy_flags)}")
    if view.provenance:
        lines.append(f"{indent}provenance: {', '.join(view.provenance)}")
    else:
        lines.append(f"{indent}provenance: none")
    return lines
