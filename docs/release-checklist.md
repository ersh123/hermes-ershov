1|# Self Ershov Memory Release Checklist
2|
3|This is a pre-release checklist only.
4|
5|**Do not tag, publish, or release this repo until Niko explicitly says so.**
6|Contributor documentation and GitHub templates are welcome, but they do not constitute release approval.
7|
8|## 1. First pass
9|
10|- [ ] Read `reviews/final-sanity.md`
11|- [ ] Read `brief.md`
12|- [ ] Read `specs/mvp-implementation-plan.md`
13|- [ ] Confirm no new blockers were introduced after the last QA pass
14|
15|## 2. Repo hygiene
16|
17|- [ ] `git status -sb` is clean, or only contains intentional release-facing changes
18|- [ ] `git diff --check` is clean
19|- [ ] No stray temp files, caches, or local artifacts are present
20|- [ ] No secrets, tokens, passwords, or personal paths are in docs or source
21|
22|## 3. Documentation consistency
23|
24|- [ ] `README.md` matches the current CLI and artifact layout
25|- [ ] `docs/release-integrity.md` matches the release workflow asset bundle and verification commands
26|- [ ] `brief.md` matches the current contract and non-goals
27|- [ ] `specs/mvp-implementation-plan.md` matches the shipped implementation
28|- [ ] `CHANGELOG.md` only lists features that actually exist
29|
30|## 4. Verification
31|
32|- [ ] `uv sync --locked --extra dev`
33|- [ ] `pytest -q --cov=hermes_dreaming --cov=self_ershov_memory --cov=hermes_mnemos --cov-report=term-missing:skip-covered --cov-report=xml --cov-fail-under=80`
34|- [ ] `pytest -q tests/test_pbt.py`
35|- [ ] `python -m compileall -q __init__.py src scripts`
36|- [ ] `git diff --check`
37|- [ ] `zizmor .github/workflows`
38|- [ ] `pip-audit . --strict --progress-spinner off`
39|- [ ] `pip-audit --local --skip-editable --progress-spinner off`
40|- [ ] `ruff check --select F401,F841,E731 __init__.py src scripts tests fuzzers`
41|- [ ] `python -m build`
42|- [ ] `twine check --strict dist/*.whl dist/*.tar.gz`
43|- [ ] `python scripts/generate_release_sbom.py --output dist/self-ershov-memory-sbom.spdx.json`
44|- [ ] `python scripts/generate_release_manifest.py --dist dist`
45|- [ ] `python scripts/generate_release_checksums.py --dist dist`
46|- [ ] `python scripts/verify_release_artifacts.py --dist dist`
47|- [ ] `(cd dist && sha256sum -c SHA256SUMS)`
48|- [ ] Smoke wheel and source distribution installs against all public CLI aliases
49|- [ ] Smoke `ershov providers doctor --provider offline-marker --strict` and confirm it is described as configuration readiness, not end-to-end generation
50|- [ ] Smoke the CLI with `ershov status`
51|- [ ] Smoke `ershov create`, `review`, `diff`, `validate`, `apply`, and `discard` on temp fixtures
52|- [ ] Smoke `ershov compact` on terminal artifacts
53|- [ ] Smoke `ershov nightly --no-llm`
54|- [ ] Smoke `ershov nightly --no-llm` with no eligible markers: exits `no-op`, creates no invalid empty artifact
55|- [ ] Smoke `HERMES_ERSHOV_SESSION_DB=/tmp/state.db ershov nightly --no-llm` with controlled marker input through the installed CLI
56|- [ ] Smoke the root Hermes plugin wrapper: `python scripts/hermes_plugin_smoke.py`
57|- [ ] Smoke the local fuzz harness: `pytest -q tests/test_fuzz_harness.py`
58|- [ ] Smoke `ershov install-cron`
59|- [ ] Smoke `ershov install-systemd --dry-run`
60|- [ ] After a real scheduled run, smoke the fast RC gate: `ershov soak --state-root ~/.hermes/ershov --since-hours 30 --min-successful 1 --strict-systemd`
61|- [ ] When provider readiness is blocked, smoke the secret-safe remediation output: `ershov status --release-gate --state-root ~/.hermes/ershov --require-provider deepseek --fix-plan`
62|- [ ] Before public stable promotion, smoke the default stable gate: `ershov soak --state-root ~/.hermes/ershov --since-hours 96 --min-successful 3 --strict-systemd`
63|- [ ] Smoke `ershov update --check` and the real `ershov update --no-verify` path on a disposable repo
64|- [ ] Confirm `docs/testing.md` still matches the GitHub Actions matrix
65|- [ ] Confirm local markdown links/images pass the docs guard
66|- [ ] Confirm the release workflow exports an SPDX SBOM and release manifest, and only uploads attested assets on a GitHub `release` event, without publishing to package indexes
67|- [ ] Confirm GitHub Release consumers can verify `release-manifest.json`, `SHA256SUMS`, `gh release verify-asset`, and `gh attestation verify` using `docs/release-integrity.md`
68|- [ ] Confirm the publish workflow can only publish to PyPI from a GitHub `release` event through the `pypi` environment, PyPI Trusted Publishing, OIDC, and artifact attestations
69|- [ ] Confirm the publish workflow verifies SBOM, release manifest, `SHA256SUMS`, and `scripts/verify_release_artifacts.py`, but uploads only `dist/*.whl` and `dist/*.tar.gz` to the PyPI publishing artifact
70|- [ ] Confirm Dependabot is enabled for GitHub Actions and uv-managed Python package metadata
71|- [ ] Confirm OpenSSF Scorecard is enabled and uploads SARIF to GitHub code scanning
72|- [ ] Confirm ClusterFuzzLite PR/manual fuzzing is wired to `.clusterfuzzlite/` and uses pinned actions
73|- [ ] Confirm PyPI Trusted Publishing is configured on PyPI for `.github/workflows/publish.yml` before any real PyPI release
74|- [ ] Confirm checkout steps use `persist-credentials: false` unless a job explicitly needs a persisted token
75|- [ ] Confirm workflow `uses:` actions are pinned to full commit SHAs with version comments
76|- [ ] Confirm CI, release, and publish workflows use locked uv installs and contain no `pip install` commands
77|- [ ] Confirm every GitHub Actions job has `timeout-minutes` and repeatable analysis workflows use concurrency cancellation
78|- [ ] Confirm write permissions for SARIF/code-scanning uploads are scoped to the upload/analyze job
79|
80|## 5. Release gate
81|
82|- [ ] Confirm Niko has explicitly approved release
83|- [ ] Confirm the intended version/tag is still correct
84|- [ ] Confirm nothing is half-finished in sibling worktrees or other release notes
85|- [ ] Only then consider a commit, tag, or publish step
86|
87|## Verdict rule
88|
89|- If any box is unchecked, the answer is **not released yet**.
90|- If all boxes are checked, pause and wait for explicit release approval before tagging.
91|