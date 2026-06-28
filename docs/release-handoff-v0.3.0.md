1|# Self Ershov Memory v0.3.0 Handoff
2|
3|This is the short follow-up note for the v0.3.0 release lane.
4|
5|## Read these first
6|
7|- `docs/release-notes-v0.3.0.md` for the shipped change summary
8|- `CHANGELOG.md` for the version history
9|- `docs/install-update.md` for the install and update path
10|
11|## Current release facts
12|
13|- Plugin version: `0.3.0`
14|- GitHub release: `v0.3.0`
15|- GitHub release URL: https://github.com/ersh123/self-ershov-memory/releases/tag/v0.3.0
16|- PR #3 stays separate while draft and must not be merged as part of this sprint
17|
18|## Verification gates
19|
20|- `python -m pytest -q`
21|- `git diff --check`
22|- `python3 -m build`
23|- temp-only Ershov smoke with `HERMES_ERSHOV_STATE_ROOT`, including a negative path-policy smoke that rejects `skill -> README.md` before live writeback and a source-secret preflight smoke that blocks provider calls before source serialization
24|
25|## Bottom line
26|
27|`v0.3.0` is built, verified, tagged, and published.
28|It is the Ershov Inbox release: queue-level operator review, recent-session harvest plumbing, proposal metadata surfacing, and inbox digest cron support.
29|