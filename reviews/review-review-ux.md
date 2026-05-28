# review-review-ux

Verdict: PASS with one usability defect.

What passed:
- State transitions persist correctly in artifact metadata and audit.jsonl.
- Approve/reject only touch artifact files, not live roots.
- Invalid proposal ids return a clean error and non-zero exit.
- Repeated approve/reject calls are idempotent and report "no changes".
- Audit output is readable and includes recent transitions.
- Relevant test coverage exists and the full suite passes.

Finding:
- FAIL: `src/hermes_dreaming/commands/review.py:154` overwrites the quoted `live_root_text` with an unquoted string before rendering the `summarize` command hints. That makes the `--live-root` examples break for workspace paths that contain spaces or shell-sensitive characters.

Fix:
- Remove the second `live_root_text = str(Path(artifact.workspace_root))` assignment and keep the `shlex.quote(...)` version for the command examples.
- Add a regression test that stages an artifact whose workspace root contains spaces and asserts the summary output still emits copy-paste-safe `--live-root` commands.

Tests run:
- `pytest -q tests/test_review_actions.py tests/test_apply.py tests/test_cli.py tests/test_validation.py tests/test_providers.py tests/test_report_card.py tests/test_policy.py`
- `pytest -q`
