1|# Self Ershov Memory v0.2.0 Release Notes
2|
3|Status: approved for release and shipped as `v0.2.0` on 2026-05-28.
4|
5|## What changed since v0.1.1
6|
7|- Review UX got a real decision loop: `ershov summarize <artifact>`, `ershov approve <artifact> <proposal-id|all>`, `ershov reject <artifact> <proposal-id> --reason ...`, and `ershov review --open` now make the artifact easier to inspect and act on.
8|- Approvals and rejections persist in artifact metadata and audit history. They do not touch live roots until `apply` runs.
9|- Provider output is now stricter and safer. Proposal blobs must validate before they become real proposals, and provenance has to point back to the source bundle instead of some made-up path.
10|- The digest flow is now local and deterministic. It can rank artifacts and proposals, show what changed since the last memory run, and render a weekly rollup without sending anything to Telegram by default.
11|- Onboarding is finally honest and usable. The repo now includes install/update docs, an offline quickstart, persona examples, and a safety page that spells out what Ershov can and cannot mutate.
12|- The first phase-7 slice landed as a real dogfoodable feature: `ershov report-card` now renders a redacted shareable report card from an artifact and can emit a JSON companion.
13|- Live-memory policy work added idempotence and capacity guardrails, plus test coverage that keeps the real `~/.hermes` state out of the way during verification.
14|
15|## Verification run
16|
17|Commands run during integration:
18|
19|- `python -m pytest -q`
20|- `python -m build`
21|- `git diff --check`
22|- docs grep for stale PyPI claims and false release text
23|
24|Results:
25|
26|- full test suite passed
27|- build passed
28|- diff check passed
29|- docs stayed honest about the PyPI namespace collision and did not claim a PyPI release
30|
31|## Packaging and distribution notes
32|
33|- PyPI is still skipped. The current release pipeline builds distributions and uploads them to GitHub Releases; PyPI publishing needs a separate token and release policy.
34|- The `self-ershov-memory` package name was chosen for the public project line. Re-check PyPI before enabling PyPI upload.
35|- GitHub release/tag creation is handled in this shipping step for `v0.2.0`.
36|
37|## Release verdict
38|
39|This is the next obvious release after `v0.1.1`.
40|It is materially better for both Niko and external users, and it is now the shipped `v0.2.0` line.
41|