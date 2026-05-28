# Hermes Dreaming v0.1.1 Release Notes

Status: approved for release by Tony and shipped as `v0.1.1`.

## What changed since v0.1.0

- Real review diffs: `dreaming diff` now shows unified diffs against `--live-root` or the artifact workspace root instead of only dumping the staged report.
- Safer apply: artifact apply now preflights selected proposals, snapshots touched files up front, rolls back on write or verification failure, and persists audit fields.
- Better audit trail: artifacts now record apply start and finish timestamps, applied proposal ids, backup paths, validation errors, and apply errors.
- Offline quickstart: `examples/quickstart/` plus `docs/quickstart.md` gives users a no-API-key review -> diff -> validate -> apply -> status demo.
- Cleaner tests and demos: pytest isolates Dreaming state, and `HERMES_DREAMING_STATE_ROOT` lets quickstart/demo runs avoid the real `~/.hermes/dreaming` run ledger.
- Safe updates: `dreaming update` supports fast-forward plugin updates with dirty-tree protection and optional pytest verification.
- Plugin packaging: the repo installs as the `hermes-dreaming` Hermes plugin and bundles the Dreaming skill.

## Packaging and versioning

- Package version: `0.1.1`
- `src/hermes_dreaming/__init__.py` exports `__version__ = "0.1.1"`
- `pyproject.toml` pins `version = "0.1.1"`
- `CHANGELOG.md` has a dedicated `0.1.1` section

## Verification run

Commands executed during release prep:

- `git diff --check`
- `python -m pytest -q`
- `python -m build`
- fresh GitHub install smoke from `main`

Results:

- `git diff --check` passed cleanly
- `pytest` passed: 60 tests
- source distribution and wheel build passed
- GitHub install smoke passed

## Release verdict

`v0.1.1` is the first usable release candidate for external users who want a staged, reviewable Dreaming loop instead of silent memory mutation.
