# Hermes Ershov quickstart

This demo is offline. It uses the default `offline-marker` provider, so no API key or external model access is required.

## Fixture paths

- Live root: `examples/quickstart/live`
- Source root: `examples/quickstart/sources`
- Artifact root: `${TMPDIR:-/tmp}/hermes-ershov-quickstart/artifacts`
- Backup root: `${TMPDIR:-/tmp}/hermes-ershov-quickstart/backups`

## Copy/paste demo

Run this from the repository root.

If the `ershov` entrypoint is not installed yet, replace it with `python -m hermes_ershov` in the commands below.
If you are inside Hermes with the plugin enabled, `hermes ershov review` uses the same flow.

```bash
export DEMO_ROOT="$(pwd)/examples/quickstart"
export LIVE_ROOT="$DEMO_ROOT/live"
export SOURCE_ROOT="$DEMO_ROOT/sources"
export ARTIFACT_ROOT="${TMPDIR:-/tmp}/hermes-ershov-quickstart/artifacts"
export BACKUP_ROOT="${TMPDIR:-/tmp}/hermes-ershov-quickstart/backups"
export HERMES_ERSHOV_STATE_ROOT="${TMPDIR:-/tmp}/hermes-ershov-quickstart/state"
export REVIEW_LOG="${TMPDIR:-/tmp}/hermes-ershov-quickstart-review.log"

mkdir -p "$ARTIFACT_ROOT" "$BACKUP_ROOT" "$HERMES_ERSHOV_STATE_ROOT"

ershov review \
  --live-root "$LIVE_ROOT" \
  --artifact-root "$ARTIFACT_ROOT" \
  --source "$SOURCE_ROOT" | tee "$REVIEW_LOG"

ARTIFACT_DIR="$(awk -F': ' '/^artifact: / {print $2; exit}' "$REVIEW_LOG")"

ershov review --open "$ARTIFACT_DIR"
ershov summarize "$ARTIFACT_DIR"
ershov approve "$ARTIFACT_DIR" all
# Optional example, uncomment to record a rejected proposal instead of approving it:
# ershov reject "$ARTIFACT_DIR" <proposal-id> --reason "too broad"
ershov diff "$ARTIFACT_DIR" --live-root "$LIVE_ROOT"
ershov validate "$ARTIFACT_DIR" --live-root "$LIVE_ROOT"
ershov apply "$ARTIFACT_DIR" --live-root "$LIVE_ROOT" --backup-root "$BACKUP_ROOT"
ershov status --artifact-root "$ARTIFACT_ROOT"
```

## What success looks like

`ershov review` should print something close to:

```text
artifact: /tmp/hermes-ershov-quickstart/artifacts/2026...-<id>
status: staged
proposals: 3
mode: dry-run
validation: valid
```

`ershov review --open` should print the artifact path and the next commands.
`ershov summarize` should show the decision counts plus recent audit entries after approvals or rejections.
`ershov diff` should start with `# Hermes Ershov Diff` and then show one `## Proposal ...` block for each of these targets:

- `fact -> facts.jsonl`
- `memory -> memory.md`
- `user -> user.md`

`ershov validate` should print `artifact is valid`.

`ershov apply` should print `applied artifact: <id>` and `status: applied`.

`ershov status` should finish with an `Artifact state: applied=1` line.

## Why this is offline

The fixture uses explicit `DREAM:` compatibility markers in text files. The default offline provider accepts both `MEMORY:` and `DREAM:` markers, so it can generate proposals without any API key, model account, or network call. The walkthrough also points `HERMES_ERSHOV_STATE_ROOT` at a temp directory so the demo does not touch your normal Ershov run ledger.
