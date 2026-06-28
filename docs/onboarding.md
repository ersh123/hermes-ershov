1|# Self Ershov Memory onboarding
2|
3|Start here if you want the whole loop in one place.
4|
5|Self Ershov Memory is a staged self-improvement loop. It scans explicit source inputs, stages proposed changes in an artifact directory, and only touches live state after an explicit apply step.
6|
7|## The short path in
8|
9|1. Install the plugin or point at a local checkout.
10|2. Run the offline quickstart.
11|3. Read the persona examples if you want to see how different operators use the same loop.
12|4. Read the safety page before you point it at anything sensitive.
13|5. Use the update doc when you want to fast-forward the installed checkout safely.
14|
15|## Start with these docs
16|
17|- Install and update, `docs/install-update.md`
18|- Offline demo, `docs/quickstart.md`
19|- Persona examples, `docs/personas.md`
20|- Safety boundaries, `docs/safety.md`
21|
22|## First run (new)
23|
24|The shortest path from "what is this" to a usable artifact is now one command. `ershov create --from-sessions 5` harvests the last 5 local Hermes sessions, prints redaction stats to stdout, and stages an artifact in one step. No manual `harvest` + `create --source` two-step required.
25|
26|```bash
27|ershov create --from-sessions 5 --live-root ./live --artifact-root ./artifacts
28|```
29|
30|For a no-network run, add `--no-llm` to skip any external provider:
31|
32|```bash
33|ershov create --from-sessions 5 --no-llm --live-root ./live --artifact-root ./artifacts
34|```
35|
36|If you want a more targeted window, use `--from-since 7d` (or `12h` / `2w`):
37|
38|```bash
39|ershov create --from-since 7d --no-llm --live-root ./live --artifact-root ./artifacts
40|```
41|
42|After staging, the rest of the loop is unchanged: `summarize`, `approve`/`reject`, `validate`, `apply`. To preview the apply without touching live state, add `--dry-run`. To undo a real apply with a post-restore validation check, run `ershov revert <artifact> --yes --validate`.
43|
44|## Nightly memory loop
45|
46|For the full nightly flow, run `nightly`. It harvests recent dialogue, stages a review artifact, writes an artifact-local `NIGHTLY.md`, refreshes the latest inbox digest, compacts terminal artifacts, and records the run in `runs.jsonl` / `ERSHOV.md`.
47|
48|```bash
49|ershov nightly --live-root ./live --artifact-root ./artifacts --no-llm
50|```
51|
52|With an LLM provider, set the provider key in the runtime environment and omit `--no-llm`. The nightly loop still does not apply live memory by itself; you approve and apply explicitly after review.
53|
54|In offline `--no-llm` mode, the nightly loop is marker-driven. If the recent harvest has no eligible `MEMORY:` / `DREAM:` lines, Ershov returns a clean `no-op` and does not create an invalid empty artifact.
55|
56|To schedule the loop inside Hermes, use the cron bridge:
57|
58|```bash
59|ershov install-cron --mode nightly-memory --schedule "0 3 * * *"
60|```
61|
62|On VPS/systemd stacks, prefer the gateway-independent timer:
63|
64|```bash
65|ershov install-systemd --on-calendar "*-*-* 03:00:00"
66|```
67|
68|The systemd installer writes non-secret runtime knobs only. Put provider keys in
69|`~/.config/self-ershov-memory/nightly.secrets.env`; reinstalling the timer does not
70|touch that file.
71|
72|For deterministic smoke tests, set `HERMES_ERSHOV_SESSION_DB=/path/to/state.db` to force harvest/nightly to read a specific SessionDB-compatible SQLite file before the live Hermes SessionDB.
73|
74|After a scheduled run has had time to fire, use `soak` as the release gate:
75|
76|```bash
77|ershov soak --state-root ~/.hermes/ershov --since-hours 30 --min-successful 1 --strict-systemd
78|```
79|
80|It is read-only. It checks `runs.jsonl` for recent successful `nightly` runs, fails on recent nightly failures, verifies the user systemd timer when `--require-timer` is set, and can require the successful run to come from the installed systemd checkout/commit.
81|The timer check requires an enabled, active, loaded timer pointing at `self-ershov-memory.service` with a next scheduled elapse.
82|Use `--strict-systemd` as the release gate so dirty current checkouts, dirty scheduled-run evidence, wrong runners, wrong commits, and weak timer states cannot count as stable evidence.
83|When provider readiness is blocked, add `--require-provider deepseek --fix-plan` to `soak` or `status --release-gate` to print secret-safe remediation steps without changing files or printing key values.
84|The one-night command above is a fast release-candidate smoke. For public stable promotion, require several scheduled nights; plain `--strict-systemd` defaults to this gate:
85|
86|```bash
87|ershov soak --state-root ~/.hermes/ershov --since-hours 96 --min-successful 3 --strict-systemd
88|```
89|
90|## What to expect
91|
92|- The offline demo works without API keys or external model access.
93|- Review comes before apply.
94|- Approvals and rejections stay in the artifact until you explicitly apply.
95|- The default flow is local-first and reviewable, not a silent background write.
96|
97|If you only want one thing to copy and paste, open `docs/quickstart.md` next.
98|