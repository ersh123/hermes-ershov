# Hermes Mnemos quickstart

This demo is offline. It uses the default `offline-marker` provider, so no API key or external model access is required.

## Fixture paths

- Live root: `examples/quickstart/live`
- Source root: `examples/quickstart/sources`
- Artifact root: `${TMPDIR:-/tmp}/hermes-mnemos-quickstart/artifacts`
- Backup root: `${TMPDIR:-/tmp}/hermes-mnemos-quickstart/backups`

## Copy/paste demo

Run this from the repository root.

If the `mnemos` entrypoint is not installed yet, replace it with `python -m hermes_mnemos` in the commands below.
If you are inside Hermes with the plugin enabled, `hermes mnemos review` uses the same flow.

```bash
export DEMO_ROOT="$(pwd)/examples/quickstart"
export LIVE_ROOT="$DEMO_ROOT/live"
export SOURCE_ROOT="$DEMO_ROOT/sources"
export ARTIFACT_ROOT="${TMPDIR:-/tmp}/hermes-mnemos-quickstart/artifacts"
export BACKUP_ROOT="${TMPDIR:-/tmp}/hermes-mnemos-quickstart/backups"
export HERMES_MNEMOS_STATE_ROOT="${TMPDIR:-/tmp}/hermes-mnemos-quickstart/state"
export REVIEW_LOG="${TMPDIR:-/tmp}/hermes-mnemos-quickstart-review.log"

mkdir -p "$ARTIFACT_ROOT" "$BACKUP_ROOT" "$HERMES_MNEMOS_STATE_ROOT"

mnemos review \
  --live-root "$LIVE_ROOT" \
  --artifact-root "$ARTIFACT_ROOT" \
  --source "$SOURCE_ROOT" | tee "$REVIEW_LOG"

ARTIFACT_DIR="$(awk -F': ' '/^artifact: / {print $2; exit}' "$REVIEW_LOG")"

mnemos review --open "$ARTIFACT_DIR"
mnemos summarize "$ARTIFACT_DIR"
mnemos approve "$ARTIFACT_DIR" all
# Optional example, uncomment to record a rejected proposal instead of approving it:
# mnemos reject "$ARTIFACT_DIR" <proposal-id> --reason "too broad"
mnemos diff "$ARTIFACT_DIR" --live-root "$LIVE_ROOT"
mnemos validate "$ARTIFACT_DIR" --live-root "$LIVE_ROOT"
mnemos apply "$ARTIFACT_DIR" --live-root "$LIVE_ROOT" --backup-root "$BACKUP_ROOT"
mnemos status --artifact-root "$ARTIFACT_ROOT"
```

## What success looks like

`mnemos review` should print something close to:

```text
artifact: /tmp/hermes-mnemos-quickstart/artifacts/2026...-<id>
status: staged
proposals: 4
mode: dry-run
validation: valid
```

`mnemos review --open` should print the artifact path and the next commands.
`mnemos summarize` should show the decision counts plus recent audit entries after approvals or rejections.
`mnemos diff` should start with `# Hermes Mnemos Diff` and then show one `## Proposal ...` block for each of these targets:

- `fact -> facts.jsonl`
- `memory -> memory.md`
- `skill -> skills/review.md`
- `user -> user.md`

`mnemos validate` should print `artifact is valid`.

`mnemos apply` should print `applied artifact: <id>` and `status: applied`.

`mnemos status` should finish with an `Artifact state: applied=1` line.

## Why this is offline

The fixture uses explicit `MEMORY:` lines in text files. That means the default offline provider can generate proposals without any API key, model account, or network call. The walkthrough also points `HERMES_MNEMOS_STATE_ROOT` at a temp directory so the demo does not touch your normal Mnemos run ledger.
