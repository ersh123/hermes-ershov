1|# Self Ershov Memory quickstart
2|
3|This demo is offline. It uses the default `offline-marker` provider, so no API key or external model access is required.
4|
5|## Fixture paths
6|
7|- Fixture root: `examples/quickstart`
8|- Demo root: a fresh `${TMPDIR:-/tmp}/self-ershov-memory-quickstart.*` directory
9|- Live root: `$DEMO_ROOT/live`
10|- Source root: `$DEMO_ROOT/sources`
11|- Artifact root: `$DEMO_ROOT/artifacts`
12|- Backup root: `$DEMO_ROOT/backups`
13|
14|## Copy/paste demo
15|
16|Run this from the repository root.
17|
18|If the `ershov` entrypoint is not installed yet, replace it with `python -m self_ershov_memory` in the commands below.
19|If you are inside Hermes with the plugin enabled, `ershov review` uses the same flow.
20|
21|```bash
22|export FIXTURE_ROOT="$(pwd)/examples/quickstart"
23|export DEMO_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/self-ershov-memory-quickstart.XXXXXX")"
24|export LIVE_ROOT="$DEMO_ROOT/live"
25|export SOURCE_ROOT="$DEMO_ROOT/sources"
26|export ARTIFACT_ROOT="$DEMO_ROOT/artifacts"
27|export BACKUP_ROOT="$DEMO_ROOT/backups"
28|export HERMES_ERSHOV_STATE_ROOT="$DEMO_ROOT/state"
29|export REVIEW_LOG="$DEMO_ROOT/review.log"
30|
31|cp -R "$FIXTURE_ROOT/live" "$LIVE_ROOT"
32|cp -R "$FIXTURE_ROOT/sources" "$SOURCE_ROOT"
33|mkdir -p "$ARTIFACT_ROOT" "$BACKUP_ROOT" "$HERMES_ERSHOV_STATE_ROOT"
34|
35|ershov review \
36|  --live-root "$LIVE_ROOT" \
37|  --artifact-root "$ARTIFACT_ROOT" \
38|  --source "$SOURCE_ROOT" | tee "$REVIEW_LOG"
39|
40|ARTIFACT_DIR="$(awk -F': ' '/^artifact: / {print $2; exit}' "$REVIEW_LOG")"
41|
42|ershov review --open "$ARTIFACT_DIR"
43|ershov summarize "$ARTIFACT_DIR"
44|ershov approve "$ARTIFACT_DIR" all
45|# Optional example, uncomment to record a rejected proposal instead of approving it:
46|# ershov reject "$ARTIFACT_DIR" <proposal-id> --reason "too broad"
47|ershov diff "$ARTIFACT_DIR" --live-root "$LIVE_ROOT"
48|ershov validate "$ARTIFACT_DIR" --live-root "$LIVE_ROOT"
49|ershov apply "$ARTIFACT_DIR" --live-root "$LIVE_ROOT" --backup-root "$BACKUP_ROOT" --dry-run
50|ershov apply "$ARTIFACT_DIR" --live-root "$LIVE_ROOT" --backup-root "$BACKUP_ROOT"
51|ershov status --artifact-root "$ARTIFACT_ROOT"
52|```
53|
54|## What success looks like
55|
56|`ershov review` should print something close to:
57|
58|```text
59|artifact: /tmp/self-ershov-memory-quickstart.<suffix>/artifacts/2026...-<id>
60|status: staged
61|proposals: 3
62|mode: dry-run
63|validation: valid
64|```
65|
66|`ershov review --open` should print the artifact path and the next commands.
67|`ershov summarize` should show the decision counts plus recent audit entries after approvals or rejections.
68|`ershov diff` should start with `# Self Ershov Memory Diff` and then show one `## Proposal ...` block for each of these targets:
69|
70|- `fact -> facts.jsonl`
71|- `memory -> memory.md`
72|- `user -> user.md`
73|
74|`ershov validate` should print `artifact is valid`.
75|
76|`ershov apply --dry-run` should print `apply: dry-run`, list the proposals that would land, and leave `$LIVE_ROOT` and `$BACKUP_ROOT` unchanged.
77|
78|`ershov apply` should print `applied artifact: <id>` and `status: applied`.
79|The real apply records backup evidence in `manifest.json`, so `ershov revert "$ARTIFACT_DIR" --live-root "$LIVE_ROOT" --backup-root "$BACKUP_ROOT" --yes --validate` can restore existing temp live files, remove files that were created by apply, and run a post-restore validation check during rollback testing.
80|
81|`ershov status` should finish with an `Artifact state: applied=1` line.
82|
83|## Why this is offline
84|
85|The fixture uses explicit `DREAM:` compatibility markers in text files. The default offline provider accepts both `MEMORY:` and `DREAM:` markers, so it can generate proposals without any API key, model account, or network call. The walkthrough also points `HERMES_ERSHOV_STATE_ROOT` at a temp directory so the demo does not touch your normal Ershov run ledger.
86|