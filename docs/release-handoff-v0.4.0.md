1|# Self Ershov Memory v0.4.0 — Handoff
2|
3|This is the short follow-up note for the v0.4.0 release lane.
4|
5|## Read these first
6|
7|- `docs/release-notes-v0.4.0.md` for the shipped change summary
8|- `CHANGELOG.md` for the version history
9|- `docs/install-update.md` for the install and update path
10|- `docs/safety.md` for the new revert section
11|- `docs/release-integrity.md` for release asset manifest, checksum, SBOM, and attestation verification
12|
13|## Current release facts
14|
15|- Plugin version: `0.4.0`
16|- GitHub release: NOT YET TAGGED — Niko's explicit release gate required
17|- PyPI publishing: workflow prepared through Trusted Publishing, but NOT RUN — Niko's explicit release gate and PyPI trusted publisher setup required
18|- PR #3 (`codex/ershov-exit-code-macos-path`) status: still separate, must not be merged as part of this sprint
19|
20|## What shipped
21|
22|- **Trust loop**: `ershov revert`, `apply --dry-run`, `apply --priority`, `apply --target-kind`
23|- **Friction-killer**: `create --from-sessions N`, `create --from-since 7d` (with `--recent` alias), `--no-llm`
24|- **Discovery**: `providers list`, `providers doctor`, `inbox --apply-ready`, inbox digest "Ready to apply" section
25|- **Hardening**: `reject --reason` enforced at the command layer
26|
27|## Files of note
28|
29|- `src/hermes_dreaming/apply.py` — `revert_artifact`, `ApplyDryRunReport`, filter validation, `_write_proposal` dry-run branch
30|- `src/hermes_dreaming/artifact.py` — `reverted_at`, `revert_audit_events`, ephemeral `dry_run_report` field
31|- `src/hermes_dreaming/cli.py` — `revert` subparser, `apply` flags, `inbox --apply-ready`, `providers` subparser, `--from-sessions` / `--from-since` / `--no-llm` flags, time-window parser
32|- `src/hermes_dreaming/commands/inbox.py` — `apply_ready` filter and `_is_apply_ready`
33|- `src/hermes_dreaming/commands/digest.py` — `apply_ready_count` / `apply_ready_rows` and the "Ready to apply" section in `render_inbox_digest`
34|- `src/hermes_dreaming/commands/review.py` — `reject_artifact` reason enforcement at command layer
35|- `src/hermes_dreaming/providers.py` — `list_providers`, `doctor_providers`, and provider table renderers
36|- `docs/testing.md` — release test matrix and stable soak evidence boundary
37|- `docs/release-integrity.md` — consumer-facing release asset verification runbook
38|- `tests/test_revert.py` (NEW), `tests/test_inbox.py` (NEW), extended `test_apply.py`, `test_cli.py`, `test_providers.py`, `test_review_actions.py`
39|
40|## Verification gates
41|
42|- `python -m pytest -q` (273 tests pass)
43|- `python -m pytest -q tests/test_pbt.py` (property-based safety invariants pass)
44|- `python -m pytest -q tests/test_fuzz_harness.py` (local fuzz harness seed smoke passes)
45|- coverage gate `--cov-fail-under=80` (current local total: 82.58%)
46|- `git diff --check` (clean)
47|- `zizmor .github/workflows` (GitHub Actions security lint passes; Release/Publish runtime artifact caches are disabled)
48|- `pip-audit . --strict --progress-spinner off` and `pip-audit --local --skip-editable --progress-spinner off` (known Python dependency vulnerability scans pass)
49|- `ruff check --select F401,F841,E731 __init__.py src scripts tests fuzzers` (dead-code lint passes)
50|- `python3 -m build` (succeeds)
51|- `twine check --strict dist/*.whl dist/*.tar.gz` (package metadata and README rendering pass)
52|- `python scripts/generate_release_sbom.py --output dist/self-ershov-memory-sbom.spdx.json` (succeeds)
53|- `python scripts/generate_release_manifest.py --dist dist` (writes `release-manifest.json`)
54|- `python scripts/generate_release_checksums.py --dist dist` (writes `SHA256SUMS`)
55|- `python scripts/verify_release_artifacts.py --dist dist` (wheel, sdist, release manifest, SBOM, and checksum bundle pass)
56|- Publish workflow parity: build job verifies SBOM, release manifest, `SHA256SUMS`, and release artifacts, then uploads only wheel/source-distribution files to the PyPI publishing artifact
57|- Console packaging: wheel and source-distribution smokes cover the package-name `self-ershov-memory` alias in addition to `ershov` and legacy aliases, using `uv --no-cache` to avoid stale ephemeral envs
58|- `docs/release-integrity.md` (documents release manifest, checksum, SBOM, `gh release verify-asset`, `gh attestation verify`, and stable-soak boundaries)
59|- Temp-only Ershov smoke with `HERMES_ERSHOV_STATE_ROOT`:
60|  - `status --release-gate --fix-plan` shows stable blockers, last nightly rows, timer health, next scheduled elapse, and secret-safe provider remediation
61|  - apply→revert roundtrip on a real fixture
62|  - `revert --validate` pass/fail audit paths
63|  - revert without `--validate` reports `post_revert_validation: not-run`
64|  - post-apply sha no-drift and drift audit paths
65|  - revert on a non-applied artifact raises and leaves live state untouched
66|  - revert with a missing backup fails loud
67|  - revert with live drift still restores from backup and records the event; legacy drift fallback is marked `legacy-degraded`
68|  - `apply --dry-run` writes nothing and produces a structured report
69|  - `apply --priority high --target-kind memory` filters correctly
70|  - `inbox --apply-ready` filters correctly
71|  - `providers list` prints the table without pinging
72|  - `providers doctor` checks local configuration readiness and timer-visible env files without network calls, model pings, or secret output; `--fix-plan` prints read-only remediation steps
73|  - `status --release-gate --fix-plan` and `soak --strict-systemd --fix-plan` surface timer-visible provider readiness and secret-safe remediation; `--require-provider deepseek` blocks offline-marker drift
74|  - `create --from-sessions 5` prints redaction stats and feeds the bundle
75|  - provider output rejects schema-valid invented `source_quote` / `snippet` evidence
76|  - `--no-llm` overrides `--provider` to `offline-marker`
77|  - `reject` without a reason returns exit 1
78|
79|## Definition of done (for the release gate)
80|
81|- [x] `git status -sb` clean (except intentional v0.4.0 changes)
82|- [x] `git diff --check` clean
83|- [x] `pytest -q` passes (273 tests)
84|- [x] `pytest -q tests/test_pbt.py` passes
85|- [x] `pytest -q tests/test_fuzz_harness.py` passes
86|- [x] `python -m build` succeeds
87|- [x] Each new + modified command smoke-tested on temp fixtures
88|- [x] CHANGELOG, release notes, handoff all written
89|- [ ] NO tag, NO GitHub release, NO PyPI publish — Niko's call
90|- [ ] PyPI Trusted Publisher must be configured for `.github/workflows/publish.yml` / environment `pypi` before publish
91|
92|## What needs Niko's eyes
93|
94|- **Revert command behavior**: new successful applies record per-write post-apply shas in `backup_records`, so drift detection can distinguish a clean applied file from an operator edit after apply. Legacy artifacts still fall back to backup-vs-live drift comparison, but those events are labeled `legacy-degraded` in audit output and `REVERT.md`.
95|- **Provider doctor behavior**: `providers doctor --strict` is a local configuration gate only. With `--from-systemd`, it checks the default Self Ershov Memory systemd `EnvironmentFile` paths the timer will see; repeatable `--env-file` remains available for explicit layouts; `--fix-plan` prints secret-safe remediation commands and `<secret>` placeholders without changing files. These paths avoid prompt/model calls, never print secret values, and fail closed when explicit `--provider` disagrees with `HERMES_ERSHOV_PROVIDER`. It is not an end-to-end generation test.
96|- **Update command behavior**: `ershov update` still refuses dirty/diverged branches and rolls back failed verification, but now retries one transient network/timeout failure during `git fetch` or `git pull --ff-only`; `--git-timeout-seconds` can be raised for slow VPS/GitHub links.
97|- **Apply filter behavior**: filtered-out proposals stay `approved` so a later apply with a different filter can still land them. This is the right behavior for the use case, but it's a state-machine subtlety. Read `apply_artifact` to confirm.
98|- **Re-run of reject without reason**: the CLI now exits 1 instead of erroring in argparse. If you want a different code, it's a one-liner in `cli.py`.
99|- **`--from-since` count heuristic**: 4 sessions per day, capped at 50. If you want a different default, change the constant in `_resolve_creation_sources`.
100|
101|## Bottom line
102|
103|`v0.4.0` is built, verified, and ready for the release gate. It is **not** tagged or published yet. Niko's explicit approval is required for the tag, GitHub release, and PyPI publish.
104|