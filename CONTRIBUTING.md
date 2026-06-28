1|# Contributing to Self Ershov Memory
2|
3|Self Ershov Memory is shipped, but contributor support is still being tightened up.
4|Please follow the safety and review expectations below before opening a pull request.
5|
6|## Before you start
7|
8|Read these first:
9|
10|- `README.md`
11|- `brief.md`
12|- `specs/mvp-implementation-plan.md`
13|- `docs/release-checklist.md`
14|- `reviews/final-sanity.md`
15|
16|## Local setup
17|
18|```bash
19|python -m pip install -e .[dev]
20|pytest -q
21|python -m build --wheel
22|```
23|
24|Useful smoke checks:
25|
26|```bash
27|ershov --help
28|ershov status
29|```
30|
31|## Repo rules
32|
33|- Do not tag, publish, or release anything without Niko's explicit approval.
34|- Only repo admins can create releases or tags unless Niko explicitly grants write access.
35|- Keep live roots and artifact roots separate.
36|- `.ershov/` is runtime output, not source.
37|- If you touch memory, user, skill, or fact writeback behavior, include provenance and tests.
38|- Do not put secrets, private tokens, passwords, or personal data into docs, fixtures, examples, or proposal text.
39|- If you change apply, discard, validation, or backup behavior, add or update tests.
40|- Keep PRs small enough that a human can review them without squinting.
41|
42|## Pre-merge checklist
43|
44|- [ ] `git diff --check`
45|- [ ] `pytest -q`
46|- [ ] `python -m build --wheel`
47|- [ ] no secrets or private data in the diff
48|- [ ] docs updated if behavior changed
49|- [ ] release-facing text reviewed if you touched user-visible commands or safety rules
50|
51|## Where to open changes
52|
53|Use the issue templates under `.github/ISSUE_TEMPLATE/` for bugs, feature requests, and docs fixes.
54|If the change affects writeback safety or release behavior, call that out explicitly in the issue or PR.
55|