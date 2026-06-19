from __future__ import annotations

from pathlib import PurePosixPath

from hypothesis import given, settings, strategies as st

from hermes_dreaming.commands.install_systemd import _env_quote, _single_line_unit_value
from hermes_dreaming.commands.soak import _commit_matches
from hermes_dreaming.providers import doctor_providers, render_provider_doctor_table
from hermes_dreaming.scoring import (
    ADD_MIN_SCORE,
    REMOVE_MIN_CONFIDENCE,
    REPLACE_MIN_SCORE,
    REPLACE_MIN_SUPERSESSION_CONFIDENCE,
    ProposedOp,
    validate_op,
)
from hermes_dreaming.validation import _safe_relative_path


_PATH_PART = st.text(
    alphabet=st.characters(blacklist_characters="/\\\x00\r\n", blacklist_categories=("Cs",)),
    min_size=1,
    max_size=12,
).filter(lambda value: value not in {".", ".."})
_GIT_HEX = st.text(alphabet="0123456789abcdef", min_size=1, max_size=40)


@settings(max_examples=250)
@given(st.lists(_PATH_PART, min_size=1, max_size=5))
def test_pbt_safe_relative_paths_accept_plain_relative_parts(parts: list[str]) -> None:
    path = "/".join(parts)

    assert _safe_relative_path(path)


@settings(max_examples=250)
@given(st.lists(_PATH_PART, min_size=1, max_size=5), st.sampled_from(["../", "/"]))
def test_pbt_safe_relative_paths_reject_escape_forms(parts: list[str], prefix: str) -> None:
    path = prefix + "/".join(parts)

    assert not _safe_relative_path(path)


@settings(max_examples=250)
@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=80))
def test_pbt_env_quote_is_single_line_and_wrapped(value: str) -> None:
    quoted = _env_quote(value)

    assert quoted.startswith('"')
    assert quoted.endswith('"')
    assert "\n" not in quoted
    assert "\r" not in quoted
    assert "$" not in quoted or "\\$" in quoted


@settings(max_examples=200)
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=32))
def test_pbt_provider_doctor_reports_key_presence_without_secret_output(suffix: str) -> None:
    secret = f"sk-secret-{suffix}"

    rows = doctor_providers(provider="deepseek", env={"DEEPSEEK_API_KEY": secret}, openai_available=True)
    output = render_provider_doctor_table(rows)

    assert rows[0].readiness == "ready"
    assert "DEEPSEEK_API_KEY: present" in output
    assert "sk-secret-" not in output


@settings(max_examples=200)
@given(st.text(alphabet=st.characters(blacklist_characters="\r\n", blacklist_categories=("Cs",)), max_size=80))
def test_pbt_systemd_unit_values_accept_single_line(value: str) -> None:
    assert _single_line_unit_value("value", value) == value


@settings(max_examples=200)
@given(
    st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=30),
    st.sampled_from(["\n", "\r", "\r\n"]),
    st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=30),
)
def test_pbt_systemd_unit_values_reject_line_breaks(prefix: str, separator: str, suffix: str) -> None:
    try:
        _single_line_unit_value("value", prefix + separator + suffix)
    except ValueError as exc:
        assert "single line" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("line breaks must be rejected")


@settings(max_examples=200)
@given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
def test_pbt_add_score_gate_matches_threshold(score: float) -> None:
    result = validate_op(
        ProposedOp(
            op="add",
            target="memory",
            old_text=None,
            new_text="- New memory.",
            reason="source-backed",
            sources=["session:1"],
            score=score,
        )
    )

    assert result.ok is (score >= ADD_MIN_SCORE)


@settings(max_examples=200)
@given(
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_pbt_replace_gates_score_and_supersession(score: float, confidence: float) -> None:
    result = validate_op(
        ProposedOp(
            op="replace",
            target="memory",
            old_text="- Old memory.",
            new_text="- New memory.",
            reason="newer source supersedes old",
            sources=["session:2"],
            score=score,
            supersession_confidence=confidence,
        )
    )

    assert result.ok is (score >= REPLACE_MIN_SCORE and confidence >= REPLACE_MIN_SUPERSESSION_CONFIDENCE)


@settings(max_examples=200)
@given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
def test_pbt_remove_gate_uses_supersession_confidence(confidence: float) -> None:
    result = validate_op(
        ProposedOp(
            op="remove",
            target="memory",
            old_text="- Stale memory.",
            new_text=None,
            reason="confirmed stale",
            sources=["session:3"],
            score=0.0,
            supersession_confidence=confidence,
        )
    )

    assert result.ok is (confidence >= REMOVE_MIN_CONFIDENCE)


@settings(max_examples=200)
@given(_GIT_HEX.filter(lambda value: len(value) < 7), st.text(alphabet="0123456789abcdef", min_size=7, max_size=40))
def test_pbt_soak_rejects_too_short_required_commit_prefix(required: str, ledger_suffix: str) -> None:
    ledger_commit = (required + ledger_suffix)[:40]

    assert not _commit_matches({"git_commit": ledger_commit}, required_commit=required)


@settings(max_examples=200)
@given(st.text(alphabet="0123456789abcdef", min_size=7, max_size=40))
def test_pbt_soak_accepts_normal_git_commit_prefixes(commit: str) -> None:
    required = commit[:7]

    assert _commit_matches({"git_commit": commit}, required_commit=required)


@settings(max_examples=120)
@given(st.lists(_PATH_PART, min_size=1, max_size=4))
def test_pbt_pure_posix_join_does_not_introduce_escape(parts: list[str]) -> None:
    path = PurePosixPath(*parts)

    assert _safe_relative_path(path.as_posix())
