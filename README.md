# hermes-dreaming

[![CI](https://github.com/asimons81/hermes-dreaming/actions/workflows/ci.yml/badge.svg)](https://github.com/asimons81/hermes-dreaming/actions/workflows/ci.yml)

![Hermes Dreaming hero banner](assets/readme/hermes-dreaming-hero.png)

A standalone, open-source staged self-improvement engine for Hermes-style memory, user, skill, and fact updates.
It scans explicit source inputs, stages proposed changes in a reviewable artifact directory, and only writes to live state after an explicit apply step.

## Hermes plugin

This repo now ships as a proper Hermes plugin too.

Install from GitHub with:

```bash
hermes plugins install asimons81/hermes-dreaming --enable
```

For a local checkout during development:

```bash
hermes plugins install file:///path/to/hermes-dreaming --enable
```

Once installed, use:

```bash
hermes dreaming review --help
```

Update the installed checkout with:

```bash
hermes dreaming update
```

Use `hermes dreaming update --check` if you only want the status check.

The plugin also bundles a Hermes skill named `dreaming`. Load that bare name inside Hermes if you want the guided staged workflow.

## Onboarding docs

- `docs/onboarding.md` is the shortest path from "what is this" to the full loop.
- `docs/install-update.md` covers plugin install and safe fast-forward updates.
- `docs/quickstart.md` is the copy/paste offline demo.
- `docs/personas.md` shows how different operators use the same loop.
- `docs/safety.md` spells out what Dreaming can and cannot mutate.

## Current status

- **Full feature set:** create, review/open, summarize, approve, reject, diff, validate, apply, discard, compact, report-card, install-cron, status, update, all implemented
- **Live memory mutation** with score gating, idempotence, backups, and capacity enforcement
- **Run ledger + DREAMS.md diary** for auditability
- **Hermes-native plugin:** install once, use everywhere
- **Recent-session reader** with fallback chain (SessionDB → SQLite → pointer-log)
- **Cron installer** for nightly dry-run review
- **Test suite passes locally**

## Install

For end-user installs, use the plugin path in `docs/install-update.md`. For local development:

```bash
python -m pip install -e .[dev]
```

If you want the optional OpenAI-compatible provider:

```bash
python -m pip install -e .[llm]
```

## CLI

```bash
# Create an artifact from sources

dreaming create --live-root ./live --artifact-root ./artifacts --source ./sources

# Review: create and validate without applying

dreaming review --live-root ./live --artifact-root ./artifacts --source ./sources

# Open an existing artifact and print next steps

dreaming review --open ./artifacts/<artifact-id>

dreaming summarize ./artifacts/<artifact-id>
dreaming approve ./artifacts/<artifact-id> all
dreaming reject ./artifacts/<artifact-id> <proposal-id> --reason "too broad"

# Inspect an artifact

dreaming diff ./artifacts/<artifact-id> --live-root ./live

# Validate a staged artifact

dreaming validate ./artifacts/<artifact-id> --live-root ./live

# Apply approved changes

dreaming apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
# Preview the apply without writing live state or creating backups
dreaming apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups --dry-run
# Apply only high-priority memory and user updates, skip skills and facts
dreaming apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups --priority high --target-kind memory,user
# Undo an apply: restore live files from the recorded backups
dreaming revert ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups --yes
# Discard a staged artifact
dreaming discard ./artifacts/<artifact-id> --archive-root ./archive
# Show artifacts that are approved and ready to apply
dreaming inbox --artifact-root ./artifacts --apply-ready
# List available analysis providers
dreaming providers list
# Stage from the last 5 local sessions in one step (replaces manual harvest + create)
dreaming create --from-sessions 5 --live-root ./live --artifact-root ./artifacts

dreaming discard ./artifacts/<artifact-id> --archive-root ./archive

# Compact terminal (applied/discarded) artifacts to an archive

dreaming compact --artifact-root ./artifacts --archive-root ./archive

# Install a nightly review-only cron job

dreaming install-cron --schedule "0 3 * * *"

# Render a local operator digest

dreaming digest ./artifacts/<artifact-id> --weekly

# Show artifact status

dreaming status --artifact-root ./artifacts

# Safely update the installed checkout

dreaming update
dreaming update --check
```

## Quickstart demo fixture

If you want the shortest path to "oh, I get it," use `examples/quickstart/`. It is an offline fixture, so no API key or external model access is required.
If the `dreaming` entrypoint is not installed yet, swap in `python -m hermes_dreaming` for the same commands.

- Fixture notes: `examples/quickstart/README.md`
- Onboarding path: `docs/onboarding.md`
- Install and update: `docs/install-update.md`
- Runnable walkthrough: `docs/quickstart.md`
- Persona examples: `docs/personas.md`
- Safety boundaries: `docs/safety.md`

### Command notes
- `report-card` renders a redacted shareable summary from an existing artifact and can write a JSON companion with `--json`.
- `digest` renders a local operator brief to stdout only. It can include `--weekly` rollups, but it does not send anything to Telegram. If you want delivery later, wrap the command in a separate transport layer that consumes stdout.
- `create` and `review` accept repeatable `--source`, `--from-sessions N` (or `--recent N` alias), `--from-since 7d`, and `--no-llm` (shorthand for `--provider offline-marker`). Harvest stats (`sessions`, `redactions`) print to stdout before staging. `review --open` prints the artifact path and the next commands.
- `apply` accepts `--dry-run` for previews, `--priority low,normal,high` to filter proposals, and `--target-kind memory,user,skill,fact` to filter by destination. Filters compose; filtered-out proposals stay approved so a later apply with a different filter can still land them.
- `revert` restores live files from the recorded backups and rolls the artifact back from `applied` to `reverted`. Requires `--yes` for non-interactive use. Drift detection records an audit event when the live file changed after apply, but the restore still runs.
- `inbox` supports `--apply-ready` to show only artifacts where every proposal is approved (or already applied) and the artifact is in `staged`, `approved`, or `applied` status. The inbox digest also surfaces a "Ready to apply" section.
- `providers list` introspects the three built-in providers (offline-marker, openai-compatible, ollama) without pinging external services. `--no-llm` is a shorthand for `--provider offline-marker` on `create` and `review`.
- OpenAI-compatible and Ollama providers fail closed on malformed output, and each proposal must carry confidence, snippet, provenance, and approved fields before it can be written.
- `summarize` prints a concise decision brief for an existing artifact.
- `approve` and `reject` update artifact metadata only, they do not touch live roots. `reject` requires a non-empty `--reason` at the command layer; any code path (CLI, library, plugin) is constrained by the same rule.
- `diff` accepts optional `--live-root` and renders unified diffs when the live target root is available.
- `apply` applies already approved proposals. `--approve` still works as a compatibility shortcut for recording approvals before apply.
- `update` supports `--remote`, `--branch`, `--check`, and `--no-verify`.

## Dream markers

The offline provider looks for explicit `DREAM:` lines in the source bundle.

```text
DREAM: memory: Keep updates short and concrete.
DREAM: user: Prefer concise status updates.
DREAM: fact: {"type": "preference", "key": "tone", "value": "casual"}
DREAM: skill: path=skills/review.md | Preserve review gates and backups.
```

## Artifact layout

Each run writes a staged artifact directory containing:

- `manifest.json`
- `REPORT.md`
- `sources.jsonl`
- `proposals.jsonl`
- `audit.jsonl`

The artifact is intentionally simple, deterministic, and easy to review on disk or in git.

## Repo docs

- `CONTRIBUTING.md` is the contributor guide and local workflow contract
- `SECURITY.md` covers private vulnerability reporting
- `CODE_OF_CONDUCT.md` sets the collaboration rules
- `brief.md` has the project brief and non-goals
- `specs/mvp-implementation-plan.md` describes the current implementation contract and package layout
- `docs/release-checklist.md` is the pre-release checklist
- `reviews/final-sanity.md` records the most recent QA pass
- `research/upstream-overlap.md` captures the upstream overlap notes and references

## Contributing

If you want to contribute, start with `CONTRIBUTING.md`.

- Use the issue templates so the scope and intent are clear.
- Run `pytest -q`, `python -m build --wheel`, and `git diff --check` before requesting review.
- If your change touches live roots, artifact roots, or writeback behavior, state that explicitly.
- If you change release-facing text or safety rules, make sure the docs still match shipped behavior.

## Development

```bash
pytest -q
python -m pip install build
python -m build --wheel
```

The repo is intentionally self-contained and safe for public release review.
