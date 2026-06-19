# Live memory policy review

Current status: RESOLVED.

Resolved by:
- `reviews/policy-wiring-review.md`
- `reviews/live-policy-scope-review.md`
- `tests/test_policy.py`
- `tests/test_provider_failure.py`
- `tests/test_validation.py`
- `tests/test_apply_memory_op.py`

Historical verdict: STOP

## What I checked

I reviewed the policy layer in `src/hermes_dreaming/policy.py`, the validation path in `src/hermes_dreaming/validation.py`, the live mutator in `src/hermes_dreaming/tools/apply_memory_op.py`, and the proposal generation path in `src/hermes_dreaming/analyze.py` / `src/hermes_dreaming/providers.py`.

I also ran:

- `pytest -q tests/test_policy.py tests/test_validation.py tests/test_review_actions.py tests/test_review_compact_cron.py tests/test_apply_memory_op.py tests/test_cli.py tests/test_providers.py`

## Findings

### 1) Idempotence keys are not wired into the real proposal pipeline

The policy layer can compute durable keys, but the actual pipeline never stamps proposals before validation:

- `src/hermes_dreaming/analyze.py:12` imports `stamp_proposal`, but `create_dream_artifact()` never calls it.
- `src/hermes_dreaming/providers.py:309-323` returns `DreamProposal.from_dict(...)` with no `idempotence_key` or `policy_version` fields.
- `src/hermes_dreaming/validation.py:73-78` only checks for key collisions if `proposal.idempotence_key` is already present.

Result: the key-based dedupe path is effectively dead in normal runs. The queue can still accept duplicate or colliding proposals because the field is never populated.

I also verified a second bug inside the stamping helper itself: `stamp_proposal()` hashes raw fact JSON text, while `evaluate_proposal()` canonicalizes fact JSON before hashing. Two semantically identical fact payloads with different key order produce different stamped keys, while `evaluate_proposal()` produces the same key. That means even if stamping were wired in, fact proposals would not get stable keys.

Relevant code:
- `src/hermes_dreaming/policy.py:209-220`
- `src/hermes_dreaming/policy.py:309-325`

### 2) The short, reviewable queue policy is documented but not enforced

`src/hermes_dreaming/policy.py:456-465` defines `run_budget_summary(...)`, and the markdown renderer advertises the run budgets in `policy_thresholds_markdown()`. But there is no runtime callsite anywhere in `src/` that actually invokes the budget gate.

That means the queue-length / reviewability claim is only documentation. There is no hard stop if a run produces too many changes, adds, chars, or targets.

### 3) Stale / supersede semantics are classified but then dropped on the floor

`evaluate_live_op()` does mark fact removals as stale and emits a warning:

- `src/hermes_dreaming/policy.py:443-445`

But neither caller surfaces that signal:

- `src/hermes_dreaming/validation.py:148-159` converts the decision to a plain error list and discards warnings/lifecycle metadata.
- `src/hermes_dreaming/tools/apply_memory_op.py:221-319` returns no lifecycle or warning field in the live result.

So a stale fact removal behaves like a plain delete from the user's point of view. The policy knows the op is supposed to be treated specially, but the behavior is invisible and cannot be audited from the returned result.

## Verified

- The policy/validation/apply tests I ran passed for the live-memory path.
- The reviewed tests use `tmp_path` and explicit monkeypatched roots, so they do not touch real `~/.hermes` state.
- The broader provider test file still has 2 unrelated failures (`tests/test_providers.py`) around missing-field / provenance handling, so the overall tree is not fully green even before policy-specific review.

## Bottom line

The policy layer exists, but the important parts are not actually connected:

- proposal stamping is not in the real pipeline
- queue-budget enforcement is just a helper with no callsite
- stale fact semantics are classified but not surfaced

That makes the implementation incomplete, not just rough around the edges.
