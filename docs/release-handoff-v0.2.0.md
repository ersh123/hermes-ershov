# Hermes Dreaming v0.2.0 Handoff

This is the short follow-up note for the shipped `v0.2.0` line.

## Read these first

- `docs/release-notes-v0.2.0.md` for the shipped change summary
- `CHANGELOG.md` for the version history
- `docs/install-update.md` for the install and update path

## Install / update path

```bash
hermes plugins install asimons81/hermes-dreaming --enable
hermes dreaming review --help
hermes dreaming update
hermes dreaming update --check
```

If you are outside Hermes, the repo still exposes the `dreaming` console script for local use, and `python -m hermes_dreaming` remains the development fallback.

## Current release facts

- GitHub release: `v0.2.0`
- GitHub release URL: https://github.com/asimons81/hermes-dreaming/releases/tag/v0.2.0
- PyPI is still skipped because `hermes-dreaming` is already taken by someone else
- PR #3 is still draft and untouched

## Verification already run

- `python -m pytest -q`
- `python -m build`
- `git diff --check`
- exact-tag install smoke from `v0.2.0`

## Bottom line

`v0.2.0` is shipped, the plugin path is documented, and the repo can be installed or updated through Hermes without any PyPI dependency.
