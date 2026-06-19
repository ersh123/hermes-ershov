# Hermes Ershov quickstart fixture

This directory is a tiny offline demo workspace. It is safe to inspect and run without any API key.

## What lives here

- `live/` is the baseline workspace the demo will update.
- `sources/` contains the `DREAM:` compatibility markers that drive the offline provider.

The offline-marker provider reads those markers directly, so the fixture works with the default provider and no API key or external model access.
If the `ershov` entrypoint is not installed yet, use `python -m hermes_ershov` with the same arguments.
The walkthrough sets `HERMES_ERSHOV_STATE_ROOT` to a temp directory so the demo does not touch your normal Ershov run ledger.

For the exact review -> summarize -> approve/reject -> diff -> validate -> apply -> status walkthrough, see `docs/quickstart.md`.
For install/update, onboarding, personas, and safety, see `docs/onboarding.md`.
