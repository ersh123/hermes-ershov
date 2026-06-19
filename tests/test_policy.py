from __future__ import annotations

from hermes_dreaming.artifact import DreamProposal
from hermes_dreaming.policy import POLICY_VERSION, evaluate_proposal, stamp_proposal
from hermes_dreaming.validation import validate_proposals


def test_stamp_proposal_normalizes_text_and_stable_key() -> None:
    proposal = DreamProposal(
        id="p1",
        target_kind="memory",
        target_path="memory.md",
        mode="append_text",
        summary="Keep updates short and concrete.",
        provenance=["sessions/1.md:1"],
        proposed_text="  - Keep updates short and concrete.\r\n",
        approved=False,
    )

    stamped = stamp_proposal(proposal)
    stamped_again = stamp_proposal(
        DreamProposal(
            id="p2",
            target_kind="memory",
            target_path="memory.md",
            mode="append_text",
            summary="Keep updates short and concrete.",
            provenance=["sessions/1.md:1"],
            proposed_text="- Keep updates short and concrete.",
            approved=False,
        )
    )

    assert stamped.proposed_text == "- Keep updates short and concrete."
    assert stamped.policy_version == POLICY_VERSION
    assert stamped.idempotence_key
    assert stamped.idempotence_key == stamped_again.idempotence_key


def test_validate_proposals_accepts_skill_and_fact_targets() -> None:
    proposals = [
        DreamProposal(
            id="skill-note",
            target_kind="skill",
            target_path="skills/notes.md",
            mode="append_text",
            summary="Stage a skill note",
            provenance=["sessions/1.md:2"],
            proposed_text="## Ershov note\n\n- Keep the skill note crisp.\n",
            approved=False,
        ),
        DreamProposal(
            id="fact-note",
            target_kind="fact",
            target_path="facts.jsonl",
            mode="jsonl_append",
            summary="Append a fact",
            provenance=["sessions/1.md:3"],
            proposed_text='{"key": "tone", "value": "direct"}',
            approved=False,
        ),
    ]

    assert validate_proposals(proposals) == []


def test_evaluate_proposal_marks_stale_fact_payloads() -> None:
    proposal = DreamProposal(
        id="fact-stale",
        target_kind="fact",
        target_path="facts.jsonl",
        mode="jsonl_append",
        summary="Mark a fact stale",
        provenance=["sessions/1.md:4"],
        proposed_text='{"key": "tone", "status": "stale"}',
        approved=False,
    )

    decision = evaluate_proposal(proposal)

    assert decision.ok is True
    assert decision.lifecycle == "stale"


def test_validate_proposals_rejects_kind_escape_paths() -> None:
    def proposal(kind: str, target_path: str, *, mode: str = "append_text", proposed_text: str = "- Probe note.") -> DreamProposal:
        return DreamProposal(
            id=f"{kind}-{target_path.replace('/', '-')}",
            target_kind=kind,
            target_path=target_path,
            mode=mode,
            summary="Probe unsafe target path handling",
            provenance=["sessions/1.md:9"],
            proposed_text=proposed_text,
            approved=False,
        )

    cases = [
        proposal("skill", "README.md"),
        proposal("skill", "skills/nested/review.md"),
        proposal("skill", "skills/.hidden.md"),
        proposal("fact", "docs/notes.jsonl", mode="jsonl_append", proposed_text='{"key":"tone"}'),
        proposal("fact", "other-facts.jsonl", mode="jsonl_append", proposed_text='{"key":"tone"}'),
    ]

    for item in cases:
        errors = validate_proposals([item])
        assert errors, item.target_path
        assert any("not allowed" in error or "unsafe target path" in error for error in errors)


def test_evaluate_proposal_rejects_kind_escape_paths() -> None:
    bad_skill = DreamProposal(
        id="skill-readme",
        target_kind="skill",
        target_path="README.md",
        mode="append_text",
        summary="Probe unsafe skill target",
        provenance=["sessions/1.md:10"],
        proposed_text="## Unsafe note\n\n- Do not allow this.\n",
        approved=False,
    )
    bad_fact = DreamProposal(
        id="fact-docs",
        target_kind="fact",
        target_path="docs/notes.jsonl",
        mode="jsonl_append",
        summary="Probe unsafe fact target",
        provenance=["sessions/1.md:11"],
        proposed_text='{"key":"tone"}',
        approved=False,
    )

    skill_decision = evaluate_proposal(bad_skill)
    fact_decision = evaluate_proposal(bad_fact)
    assert skill_decision.ok is False
    assert "unsafe target path" in skill_decision.error
    assert fact_decision.ok is False
    assert "unsafe target path" in fact_decision.error
