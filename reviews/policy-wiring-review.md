# Policy wiring review

Verdict: PASS for staged-artifact policy wiring.

What changed:
- Provider proposals are now stamped before artifact validation, so stored artifacts carry normalized text, `idempotence_key`, and `policy_version`.
- Fact proposal stamping canonicalizes JSON before key generation, matching the validation/evaluation path.
- Staged artifact creation now enforces the run-level review budget for proposal count, new text size, and touched targets.
- The quickstart fixture now emits three proposals, so the public demo stays inside the documented review budget.

Verification:
- `pytest -q tests/test_policy.py tests/test_provider_failure.py tests/test_quickstart_fixture.py`
- `python -m compileall -q __init__.py src scripts && pytest -q`
- `python -m build`
- wheel CLI smoke for `ershov`, `mnemos`, `nightmem`, `dreaming`, `python -m hermes_ershov`, and `python -m hermes_mnemos`

Remaining note:
- `max_adds_per_run` remains a live-operation budget because staged provider proposals do not encode add/replace/remove intent.
