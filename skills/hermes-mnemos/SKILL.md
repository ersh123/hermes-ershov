---
name: hermes-mnemos
description: Use when Hermes needs staged self-improvement, explicit reviewable artifacts, or safe apply/discard workflows for memory, user, skill, or fact updates.
---

# Hermes Mnemos

Use this plugin when you want staged, reviewable self-improvement instead of silent writes.

## Core idea

Hermes Mnemos scans explicit source inputs, stages proposed changes in an artifact directory, and only writes to live state after an explicit apply step. It is designed for local-first, reviewable updates.

## When to use

- You want to convert notes or `MEMORY:` markers into staged proposals.
- You want a reviewable diff before anything touches live state.
- You want explicit apply/discard gates.
- You want to keep backups and archives under separate roots.

## Main commands

```bash
mnemos create --live-root ./live --artifact-root ./artifacts --source ./sources
mnemos review --live-root ./live --artifact-root ./artifacts --source ./sources
mnemos review --open ./artifacts/<artifact-id>
mnemos summarize ./artifacts/<artifact-id>
mnemos approve ./artifacts/<artifact-id> all
mnemos reject ./artifacts/<artifact-id> <proposal-id> --reason "too broad"
mnemos diff ./artifacts/<artifact-id> --live-root ./live
mnemos validate ./artifacts/<artifact-id> --live-root ./live
mnemos apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
mnemos discard ./artifacts/<artifact-id> --archive-root ./archive
mnemos compact --artifact-root ./artifacts --archive-root ./archive
mnemos nightly --live-root ./live --artifact-root ./artifacts --no-llm
mnemos install-cron --mode nightly-memory --schedule "0 3 * * *"
mnemos install-systemd --on-calendar "*-*-* 03:00:00"
mnemos status --artifact-root ./artifacts
mnemos update
```

## Safe usage pattern

1. Keep the live root small and explicit.
2. Put generated artifacts in a separate artifact root.
3. Use `review --open` or `summarize` to understand the current decision state.
4. Use `approve` or `reject` to record human decisions without mutating live roots.
5. Use `diff` and `validate` before `apply`.
6. Use `discard` when the staged proposal is wrong or stale.

## Fast path

If you want the safest short workflow, use `review` first, then `diff`, `validate`, and `apply` only after the staged artifact looks right.

For unattended nightly runs, use `nightly`: it harvests recent dialogue, stages an artifact, writes digests, compacts terminal artifacts, and records the run ledger. It never applies live memory automatically.
On VPS/systemd stacks, prefer `install-systemd` so the nightly memory loop runs outside the Hermes gateway process.
For systemd model keys, use `~/.config/hermes-mnemos/nightly.secrets.env`; the installer does not write secrets.

## Memory marker format

The offline provider looks for explicit `MEMORY:` lines in the source bundle.

```text
MEMORY: memory: Keep updates short and concrete.
MEMORY: user: Prefer concise status updates.
MEMORY: fact: {"type": "preference", "key": "tone", "value": "casual"}
MEMORY: skill: path=skills/review.md | Preserve review gates and backups.
```

## Notes

- This plugin is local-first and does not need paid X or cloud APIs for the default offline flow.
- Use the optional LLM provider only if you explicitly want one.
- The plugin is fine without this skill file, but the skill makes the workflow much easier to remember and reuse.
