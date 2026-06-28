1|# Self Ershov Memory test matrix
2|
3|This project treats test coverage as release evidence, not just a percentage.
4|
5|## Practice baseline
6|
7|The matrix follows the current public docs for:
8|
9|- pytest good integration practices: https://docs.pytest.org/en/stable/explanation/goodpractices.html
10|- Hypothesis property-based and stateful testing: https://hypothesis.readthedocs.io/en/latest/stateful.html
11|- GitHub Actions Python build/test workflows: https://docs.github.com/actions/guides/building-and-testing-python
12|- GitHub Actions workflow syntax, timeouts, and concurrency: https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions
13|- uv GitHub Actions integration: https://docs.astral.sh/uv/guides/integration/github/
14|- uv Dependabot integration: https://docs.astral.sh/uv/guides/integration/dependabot/
15|- GitHub CodeQL workflow configuration: https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options
16|- GitHub Dependabot configuration: https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference
17|- OpenSSF Scorecard GitHub Action: https://github.com/ossf/scorecard-action
18|- OpenSSF Scorecard Fuzzing check: https://github.com/ossf/scorecard/blob/main/docs/checks.md#fuzzing
19|- ClusterFuzzLite GitHub Actions: https://google.github.io/clusterfuzzlite/running-clusterfuzzlite/github-actions/
20|- ClusterFuzzLite Python integration: https://google.github.io/clusterfuzzlite/build-integration/python-lang/
21|- PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/using-a-publisher/
22|- GitHub artifact attestations: https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds
23|- GitHub release integrity verification: https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/verifying-the-integrity-of-a-release
24|- GitHub CLI release asset verification: https://cli.github.com/manual/gh_release_verify-asset
25|- GitHub CLI artifact attestation verification: https://cli.github.com/manual/gh_attestation_verify
26|- SLSA build provenance subject/digest model: https://slsa.dev/spec/v1.2/build-provenance
27|- in-toto Statement subject/digest model: https://github.com/in-toto/attestation/blob/v1.0/spec/v1.0/statement.md
28|- SPDX package information: https://spdx.github.io/spdx-spec/v2.3/package-information/
29|- OpenSSF Scorecard Packaging: https://github.com/ossf/scorecard/blob/main/docs/checks.md#packaging
30|- pip-audit Python dependency vulnerability auditing: https://github.com/pypa/pip-audit
31|- Ruff Python linter: https://github.com/astral-sh/ruff
32|
33|## Local gates
34|
35|Run these before a release-facing change:
36|
37|```bash
38|uv sync --locked --extra dev
39|uv run --locked --extra dev python -m pytest -q --cov=hermes_dreaming --cov=self_ershov_memory --cov=hermes_mnemos --cov-report=term-missing:skip-covered --cov-report=xml --cov-fail-under=80
40|uv run --locked --extra dev python -m pytest -q tests/test_pbt.py
41|uv run --locked --extra dev python -m compileall -q __init__.py src scripts
42|git diff --check
43|uv run --locked --extra dev zizmor .github/workflows
44|uv run --locked --extra dev pip-audit . --strict --progress-spinner off
45|uv run --locked --extra dev pip-audit --local --skip-editable --progress-spinner off
46|uv run --locked --extra dev ruff check --select F401,F841,E731 __init__.py src scripts tests fuzzers
47|uv run --locked --extra dev python -m build
48|uv run --locked --extra dev twine check --strict dist/*.whl dist/*.tar.gz
49|uv run --locked --extra dev python scripts/hermes_plugin_smoke.py
50|```
51|
52|For installed-artifact confidence, smoke the wheel in a temporary virtualenv and run at least:
53|
54|```bash
55|ershov --help
56|ershov providers list
57|ershov providers doctor --provider offline-marker --strict
58|ershov providers doctor --provider offline-marker --from-systemd --strict
59|ershov providers doctor --provider deepseek --from-systemd --strict
60|ershov providers doctor --provider deepseek --from-systemd --fix-plan --strict
61|ershov providers doctor --provider deepseek --env-file ~/.config/self-ershov-memory/nightly.env --env-file ~/.config/self-ershov-memory/nightly.secrets.env --strict
62|ershov status --release-gate --state-root ~/.hermes/ershov --require-provider deepseek
63|ershov status --release-gate --state-root ~/.hermes/ershov --require-provider deepseek --fix-plan
64|ershov soak --state-root ~/.hermes/ershov --since-hours 30 --min-successful 1 --strict-systemd --require-provider deepseek
65|ershov soak --state-root ~/.hermes/ershov --since-hours 30 --min-successful 1 --strict-systemd --require-provider deepseek --fix-plan
66|ershov status --release-gate --state-root /tmp/self-ershov-memory-state
67|ershov revert --help
68|```
69|
70|The status release gate is state-root scoped: with `--state-root`, the default artifact root and ledger/diary paths come from that state root unless `--artifact-root` is passed explicitly.
71|The provider env-file smoke is timer-visible only: `--from-systemd` reads the default Self Ershov Memory systemd `EnvironmentFile` paths, explicit `--env-file` values can test non-default layouts, missing optional secret files are ignored, and secret values are never printed. When `--provider` is explicit, `providers doctor` also fails closed if `HERMES_ERSHOV_PROVIDER` points at a different timer provider. `--fix-plan` is still read-only across `providers doctor`, `status --release-gate`, and text-mode `soak`; it prints remediation commands and `<secret>` placeholders only. `--require-provider deepseek` is stricter than readiness alone: it also fails when the timer is still configured for `offline-marker`.
72|
73|## CI gates
74|
75|GitHub Actions runs the same release-shaped matrix:
76|
77|- Python 3.11, 3.12, and 3.13
78|- `uv.lock` backed dependency resolution through pinned `astral-sh/setup-uv`
79|- locked dev environment sync with `uv sync --locked --extra dev`
80|- whitespace check with `git diff --check`
81|- Zizmor GitHub Actions security lint
82|- pip-audit known-vulnerability scans for declared project dependencies and the locked local Python environment
83|- Ruff dead-code lint for unused imports, unused locals, and lambda assignments
84|- bytecode compile with `compileall`
85|- full pytest suite
86|- coverage report for `hermes_dreaming`, `self_ershov_memory`, and `hermes_mnemos`, with an 80% minimum gate
87|- property-based tests from `tests/test_pbt.py`
88|- local fuzz harness smoke from `tests/test_fuzz_harness.py`
89|- timer-visible provider readiness smoke with `providers doctor --from-systemd`, `status --release-gate --fix-plan`, `soak --fix-plan`, and explicit `--env-file`
90|- strict systemd release-gate tests that include timer-visible provider readiness and required-provider mismatch checks
91|- Hermes plugin wrapper smoke
92|- wheel and source distribution build
93|- Twine package metadata checks for the built wheel and source distribution
94|- installed wheel smoke for every public console alias (`ershov`, `self-ershov-memory`, `mnemos`, `nightmem`, `dreaming`) and module alias, with `uv --no-cache` so the check uses the freshly built artifact
95|- installed source distribution smoke for every public console alias (`ershov`, `self-ershov-memory`, `mnemos`, `nightmem`, `dreaming`) and module alias, with `uv --no-cache` so the check uses the freshly built artifact
96|- CodeQL on push, pull request, schedule, and manual dispatch
97|- Dependabot weekly version-update checks for GitHub Actions and uv-managed Python package metadata
98|- OpenSSF Scorecard on weekly schedule and manual dispatch, with SARIF uploaded to code scanning
99|- ClusterFuzzLite PR/manual fuzzing for the Python safety harness through `.clusterfuzzlite/` and `fuzzers/ershov_safety_fuzzer.py`
100|- SPDX release SBOM generation into `dist/self-ershov-memory-sbom.spdx.json`
101|- `release-manifest.json` generation for release subject names, kinds, sizes, SHA256 digests, source commit/ref, and GitHub Actions run hints
102|- `SHA256SUMS` generation for the wheel, source distribution, SPDX SBOM, and release manifest assets
103|- release artifact verification for wheel metadata, source distribution metadata, release manifest subject digests, SBOM package coverage, purl refs, locked SHA256 checksums, and root dependency relationships
104|- public release integrity runbook in `docs/release-integrity.md`, including `sha256sum -c`, `gh release verify-asset`, `gh attestation verify`, release manifest, SBOM, and stable-soak boundaries
105|- GitHub Release asset attestations on release-event uploads
106|- PyPI Trusted Publishing through OIDC on GitHub `release` events only, with GitHub artifact attestations for the built distributions
107|- checkout-token hardening through `persist-credentials: false` on repository checkout steps
108|- workflow action pinning to full commit SHAs with adjacent version comments
109|- isolated wheel and source distribution smoke through `uv run --no-cache --no-project --isolated --with dist/*`
110|- workflow install hardening: CI and release workflows avoid `pip install` and use the committed lockfile
111|- workflow-level concurrency for repeatable analysis jobs and job-level `timeout-minutes` on every GitHub Actions job
112|- job-scoped write permissions for SARIF/code-scanning uploads; top-level workflow permissions stay read-only unless the workflow has no narrower safe option
113|- release asset workflow build runs under read-only repository permissions; asset upload is isolated to a separate `release`-event-only job with `contents: write`, `id-token: write`, and `attestations: write`
114|- publish workflow build runs under read-only repository permissions; it generates and verifies the same SBOM, release manifest, checksum manifest, and artifact bundle contract before uploading only wheel/source-distribution files to the PyPI publishing artifact
115|- runtime artifact workflow cache disabled for Release and Publish jobs
116|- release-event-only PyPI publishing is isolated to a `pypi` environment job with `id-token: write` and `attestations: write`
117|
118|## Coverage shape
119|
120|The suite is intentionally mixed:
121|
122|- unit tests for pure validation, scoring, policy, memory IO, provider parsing, and artifact state
123|- CLI tests for user-facing command behavior and exit codes
124|- integration smokes for create, validate, apply, revert, status, update, nightly, and plugin wrapping
125|- property-based tests for path safety, scoring thresholds, systemd escaping, and soak commit matching
126|- ClusterFuzzLite/Atheris fuzz target coverage for path validation, env quoting, provider fact parsing, memory-op validation, and score gates
127|- docs guards that fail when release-facing text drifts from shipped behavior
128|- local markdown link/image guards for release-facing docs
129|- release workflow guards and publish workflow guards that prevent accidental release creation, accidental PyPI publishing outside the dedicated Trusted Publishing job, and accidental non-package assets in the PyPI upload artifact
130|- supply-chain workflow guards for Scorecard permissions, SARIF output, checkout token persistence, full-SHA action pinning, ClusterFuzzLite wiring, workflow timeout/concurrency controls, and top-level permission minimization
131|- negative tests for malformed provider output, fabricated provenance, fabricated quotes/snippets, unsafe paths, missing backups, and no-op nightlies
132|
133|## Stable-release evidence
134|
135|Passing CI is not enough for stable wording. Stable promotion also needs scheduled-run evidence from the installed VPS checkout:
136|
137|```bash
138|ershov soak --state-root ~/.hermes/ershov --since-hours 96 --min-successful 3 --strict-systemd
139|```
140|
141|Plain `--strict-systemd` defaults to this 96h/3-run public-stable gate and checks the configured timer provider from the systemd env files. Add `--require-provider deepseek` when the gate must prove DeepSeek specifically, not just any ready provider. Use `--since-hours 30 --min-successful 1 --strict-systemd` only for a fast one-night release-candidate smoke.
142|
143|Manual service starts and transient timer smokes are useful debug evidence, but they do not satisfy the stable gate.
144|