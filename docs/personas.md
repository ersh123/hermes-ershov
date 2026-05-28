# Hermes Dreaming persona examples

These are not separate modes. They are the same staged review loop pointed at different source bundles and live roots.

If you are inside Hermes, swap `dreaming` for `hermes dreaming` and keep the same flow.

## Solo builder

Use Dreaming when you want to turn your own notes into durable memory without mutating live state mid-thought.

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
dreaming review --live-root ./live --artifact-root ./artifacts --source ./sources
# inspect the artifact
dreaming summarize ./artifacts/<artifact-id>
# choose the right branch
dreaming approve ./artifacts/<artifact-id> all
# or
dreaming reject ./artifacts/<artifact-id> p-02 --reason "too broad"
dreaming diff ./artifacts/<artifact-id> --live-root ./live
dreaming validate ./artifacts/<artifact-id> --live-root ./live
dreaming apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
```

What to reject:

- vague cleanups with no source grounding
- giant catch-all changes that try to rewrite half the live state at once

## Social-media operator

Use Dreaming when you want to turn content experiments into durable operator rules.

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
dreaming review --live-root ./live --artifact-root ./artifacts --source ./sources/social-notes.md
dreaming summarize ./artifacts/<artifact-id>
dreaming approve ./artifacts/<artifact-id> all
dreaming diff ./artifacts/<artifact-id> --live-root ./live
dreaming validate ./artifacts/<artifact-id> --live-root ./live
dreaming apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
```

What to reject:

- content ideas dressed up as durable memory
- post drafts that are still marketing fluff instead of a real operational note

## Coding-agent maintainer

Use Dreaming when a review, test run, or CLI check surfaced a rule that should stick.

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
dreaming review --live-root ./live --artifact-root ./artifacts --source ./reviews/provider-review.md --source ./reviews/review-ux.md
dreaming summarize ./artifacts/<artifact-id>
# If the review is clean, approve the whole batch.
dreaming approve ./artifacts/<artifact-id> all
# If one proposal is wrong, reject it instead and re-run summarize.
# dreaming reject ./artifacts/<artifact-id> p-04 --reason "unsupported claim"
dreaming diff ./artifacts/<artifact-id> --live-root ./live
dreaming validate ./artifacts/<artifact-id> --live-root ./live
dreaming apply ./artifacts/<artifact-id> --live-root ./live --backup-root ./backups
```

What to reject:

- unsupported claims about flags, install steps, or provider behavior
- review notes that say "should" without proving the thing exists in the repo

## Rule of thumb

If the source bundle would embarrass you in a code review, tighten it first. Dreaming is for durable, source-grounded updates, not for turning vague advice into fake certainty.
