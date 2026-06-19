# Hermes Ershov persona examples

These are not separate modes. They are the same staged review loop pointed at different source bundles and live roots.

If you are inside Hermes, swap `ershov` for `hermes ershov` and keep the same flow.

## Solo builder

Use Ershov when you want to turn your own notes into durable memory without mutating live state mid-thought.

Good inputs:

- a couple of recent session notes
- one or two concrete preferences
- a small skill tweak that clearly belongs in the repo

Good output:

- short memory updates
- user preference updates
- one narrow skill edit
- a fact record that came from an actual source note

Example flow:

```bash
ershov review --live-root ./live --artifact-root ./artifacts --source ./sources
# inspect the artifact
ershov summarize ./artifacts/<artifact-id>
# choose the right branch
ershov approve ./artifacts/<artifact-id> all
# or
ershov reject ./artifacts/<artifact-id> p-02 --reason "too broad"
ershov diff ./artifacts/<artifact-id> --live-root ./live
ershov validate ./artifacts/<artifact-id> --live-root ./live
ershov apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
```

What to reject:

- vague cleanups with no source grounding
- giant catch-all changes that try to rewrite half the live state at once

## Social-media operator

Use Ershov when you want to turn content experiments into durable operator rules.

Good inputs:

- a draft hook that actually landed
- a short note about what flopped
- a session note about tone, cadence, or format
- a source bundle that separates real feedback from vanity metrics

Good output:

- user preference notes about tone and pacing
- skill reminders about what to repeat or stop doing
- facts that capture a real pattern, not a vibe

Example flow:

```bash
ershov review --live-root ./live --artifact-root ./artifacts --source ./sources/social-notes.md
ershov summarize ./artifacts/<artifact-id>
ershov approve ./artifacts/<artifact-id> all
ershov diff ./artifacts/<artifact-id> --live-root ./live
ershov validate ./artifacts/<artifact-id> --live-root ./live
ershov apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
```

What to reject:

- content ideas dressed up as durable memory
- post drafts that are still marketing fluff instead of a real operational note

## Coding-agent maintainer

Use Ershov when a review, test run, or CLI check surfaced a rule that should stick.

Good inputs:

- review notes with concrete file references
- a test failure that exposed a repeatable workflow problem
- command output that proved a flag, path, or install step
- a small set of linked source notes instead of a full repo dump

Good output:

- skill updates that preserve the real workflow
- facts that capture a verified command or constraint
- memory notes that keep future runs from repeating the same mistake

Example flow:

```bash
ershov review --live-root ./live --artifact-root ./artifacts --source ./reviews/provider-review.md --source ./reviews/review-ux.md
ershov summarize ./artifacts/<artifact-id>
# If the review is clean, approve the whole batch.
ershov approve ./artifacts/<artifact-id> all
# If one proposal is wrong, reject it instead and re-run summarize.
# ershov reject ./artifacts/<artifact-id> p-04 --reason "unsupported claim"
ershov diff ./artifacts/<artifact-id> --live-root ./live
ershov validate ./artifacts/<artifact-id> --live-root ./live
ershov apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
```

What to reject:

- unsupported claims about flags, install steps, or provider behavior
- review notes that say "should" without proving the thing exists in the repo

## Nightly operator

Use Ershov as the queue that closes the loop every morning. The nightly cron posts an inbox digest; you skim it, decide, and act.

Good inputs:

- the inbox digest from last night (`ershov digest --inbox` in the cron mode)
- one source of truth for what changed (recent sessions, weekly notes)
- a small, low-risk change you can stage without much review

Good output:

- nothing (most days, and that's the point)
- a single approved artifact with one or two high-confidence memory or user notes
- a clear answer to "is there anything apply-ready?"

Example flow:

```bash
# After reading the inbox digest, filter to the rows that are actually apply-ready
ershov inbox --apply-ready
# If something is there, preview the apply first
ershov apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups --dry-run
# If the dry-run looks right, apply it
ershov apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups --approve all
# If you applied something that turned out wrong, undo it
ershov revert ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups --yes
# If you only want high-priority memory/user updates today, filter the apply
ershov apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups --priority high --target-kind memory,user
```

What to reject:

- anything that needs explanation to a teammate
- "I should also fix this while I'm in there" — keep the nightly loop small
- silent network calls: pass `--no-llm` if you do not want the offline-marker provider swapped for an external LLM by accident

## Rule of thumb

If the source bundle would embarrass you in a code review, tighten it first. Ershov is for durable, source-grounded updates, not for turning vague advice into fake certainty.
