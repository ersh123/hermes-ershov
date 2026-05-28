# What Dreaming can and cannot mutate

Hermes Dreaming is staged self-improvement. It can make durable changes, but only through a reviewable artifact and an explicit apply step.

## It can mutate

- live memory files under the live root, such as `memory.md`
- live user files under the live root, such as `user.md`
- skill files under the live root, such as `skills/review.md`
- JSONL fact files under the live root
- any other safe relative path that lives inside the live root and came from an approved proposal

In the current offline fixture, the demo shows four target kinds:

- `fact`
- `memory`
- `skill`
- `user`

## It cannot mutate

- the live root during `review`, `summarize`, `diff`, or `validate`
- the source bundle itself
- paths outside the live root
- absolute paths or path traversal targets like `..`
- hidden side channels or a second source of truth

## Guard rails

- proposals are staged first, then reviewed
- `approve` and `reject` only touch artifact metadata until you apply
- `apply` validates before it writes
- backups are taken before live writes
- unsafe proposal paths are rejected instead of being normalized into something dangerous

## Practical rule

If you would not be comfortable restoring it from a backup, do not point Dreaming at it. Keep the live root boring, explicit, and easy to inspect on disk.
