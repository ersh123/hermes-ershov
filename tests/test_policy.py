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
            target_path="notes.md",
            mode="append_text",
            summary="Stage a skill note",
            provenance=["sessions/1.md:2"],
            proposed_text="## Dreaming note\n\n- Keep the skill note crisp.\n",
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
