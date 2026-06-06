# Hermes Dreaming onboarding

Start here if you want the whole loop in one place.

Hermes Dreaming is a staged self-improvement loop. It scans explicit source inputs, stages proposed changes in an artifact directory, and only touches live state after an explicit apply step.

## The short path in

1. Install the plugin or point at a local checkout.
2. Run the offline quickstart.
3. Read the persona examples if you want to see how different operators use the same loop.
4. Read the safety page before you point it at anything sensitive.
5. Use the update doc when you want to fast-forward the installed checkout safely.

## Start with these docs

- Install and update, `docs/install-update.md`
- Offline demo, `docs/quickstart.md`
- Persona examples, `docs/personas.md`
- Safety boundaries, `docs/safety.md`

## First run (new)

The shortest path from "what is this" to a usable artifact is now one command. `dreaming create --from-sessions 5` harvests the last 5 local Hermes sessions, prints redaction stats to stdout, and stages an artifact in one step. No manual `harvest` + `create --source` two-step required.

```bash
dreaming create --from-sessions 5 --live-root ./live --artifact-root ./artifacts
```

For a no-network run, add `--no-llm` to skip any external provider:

```bash
dreaming create --from-sessions 5 --no-llm --live-root ./live --artifact-root ./artifacts
```

If you want a more targeted window, use `--from-since 7d` (or `12h` / `2w`):

```bash
dreaming create --from-since 7d --no-llm --live-root ./live --artifact-root ./artifacts
```

After staging, the rest of the loop is unchanged: `summarize`, `approve`/`reject`, `validate`, `apply`. To preview the apply without touching live state, add `--dry-run`. To undo a real apply, run `dreaming revert <artifact> --yes`.

## What to expect

- The offline demo works without API keys or external model access.
- Review comes before apply.
- Approvals and rejections stay in the artifact until you explicitly apply.
- The default flow is local-first and reviewable, not a silent background write.

If you only want one thing to copy and paste, open `docs/quickstart.md` next.