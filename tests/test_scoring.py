from __future__ import annotations

from hermes_dreaming.scoring import (
    ADD_MIN_SCORE,
    REMOVE_MIN_CONFIDENCE,
    REPLACE_MIN_SCORE,
    REPLACE_MIN_SUPERSESSION_CONFIDENCE,
    ProposedOp,
    thresholds_for_prompt,
    validate_op,
)


def _make_op(**kwargs) -> ProposedOp:
    defaults = dict(
        op="add",
        target="memory",
        old_text=None,
        new_text="- New entry.",
        reason="test",
        sources=["sess-1"],
        score=0.90,
        supersession_confidence=0.0,
    )
    defaults.update(kwargs)
    return ProposedOp(**defaults)


def test_add_passes_at_threshold():
    op = _make_op(op="add", score=ADD_MIN_SCORE)
    assert validate_op(op).ok


def test_add_fails_below_threshold():
    op = _make_op(op="add", score=ADD_MIN_SCORE - 0.01)
    result = validate_op(op)
    assert not result.ok
    assert "add score" in result.error


def test_replace_requires_score_and_supersession_confidence():
    op = _make_op(
        op="replace",
        old_text="- Old entry.",
        score=REPLACE_MIN_SCORE,
        supersession_confidence=REPLACE_MIN_SUPERSESSION_CONFIDENCE,
    )
    assert validate_op(op).ok

    low_score = _make_op(
        op="replace",
        old_text="- Old entry.",
        score=REPLACE_MIN_SCORE - 0.01,
        supersession_confidence=REPLACE_MIN_SUPERSESSION_CONFIDENCE,
    )
    assert not validate_op(low_score).ok

    low_confidence = _make_op(
        op="replace",
        old_text="- Old entry.",
        score=REPLACE_MIN_SCORE,
        supersession_confidence=REPLACE_MIN_SUPERSESSION_CONFIDENCE - 0.01,
    )
    result = validate_op(low_confidence)
    assert not result.ok
    assert "supersession_confidence" in result.error


def test_remove_requires_old_text_and_confidence():
    op = _make_op(
        op="remove",
        old_text="- Old entry.",
        new_text=None,
        score=0.0,
        supersession_confidence=REMOVE_MIN_CONFIDENCE,
    )
    assert validate_op(op).ok

    missing_old = _make_op(
        op="remove",
        old_text=None,
        new_text=None,
        score=0.0,
        supersession_confidence=REMOVE_MIN_CONFIDENCE,
    )
    assert not validate_op(missing_old).ok

    low_confidence = _make_op(
        op="remove",
        old_text="- Old entry.",
        new_text=None,
        score=0.0,
        supersession_confidence=REMOVE_MIN_CONFIDENCE - 0.01,
    )
    result = validate_op(low_confidence)
    assert not result.ok
    assert "remove confidence" in result.error


def test_thresholds_table_mentions_all_operations():
    prompt = thresholds_for_prompt()
    assert "`add`" in prompt
    assert "`replace`" in prompt
    assert "`remove`" in prompt
    assert str(ADD_MIN_SCORE) in prompt
