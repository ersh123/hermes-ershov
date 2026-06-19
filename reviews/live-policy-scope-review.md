# Live policy scope review

Verdict: PASS for live mutator scope.

What changed:
- Live memory policy now explicitly supports only `memory` and `user`, matching `ershov_apply_memory_op` and `memory_io.py`.
- `fact` and `skill` writes remain staged artifact proposals, where review, validation, approval, backup, and apply flow already exist.
- The previous stale-fact live warning path is intentionally removed from the live helper because no live fact mutator exists.

Why:
- A release-grade live mutator should fail closed instead of exposing policy states for targets it cannot actually write safely.
- This keeps the fast live tool narrow and leaves broader durable writes in the reviewable artifact path.

Verification:
- `pytest -q tests/test_policy.py tests/test_validation.py tests/test_apply_memory_op.py`
