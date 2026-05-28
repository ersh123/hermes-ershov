# review-provider-hardening

Verdict: STOP — the hardening still accepts malformed provider blobs and does not actually ground provenance in real sources.

Blockers:
- `src/hermes_dreaming/providers.py:312-355` coerces arbitrary JSON values to strings before validation. That means a payload like `"proposed_text": {"blob": [1,2,3]}` is accepted as the literal string representation instead of being rejected. I reproduced this directly, so invalid structured output can still slip through and get staged.
- `src/hermes_dreaming/providers.py:271-290` and `:332-340` only require provenance to be non-empty. There is no check that the refs match the actual source bundle, so fabricated provenance like `"made-up:1"` passes unchanged. That makes the provenance field decorative, not real.

What passed:
- Missing-field provider output now fails closed instead of being silently dropped.
- Provider failures are surfaced as invalid artifacts with a visible failure report.
- The full test suite passes, but it does not cover the blob/provenance acceptance gaps above.

Tests run:
- `pytest -q tests/test_providers.py tests/test_provider_failure.py tests/test_policy.py tests/test_validation.py`
- `pytest -q`
- Manual repros for structured `proposed_text` and fabricated `provenance` acceptance via `OpenAICompatibleProvider.generate()`
