# self-ershov-memory loop state

## Goal
Implement MiMo-style controlled context rebuild in self-ershov-memory without making OpenViking canonical.

## Loop pattern
Schedule/trigger: user request in Telegram.
State: this STATE.md + tests.
Worktree: current repo `/home/niko/.hermes/plugins/hermes-ershov`.
Implementer: Debi.
Checker: pytest + ruff + coverage.
Human gate: report to Niko after verified code.

## Tasks
- [x] Inspect MiMo-Code pattern and Hermes hooks.
- [x] Add sidecar checkpoint/rebuild/FTS CLI.
- [x] Add tests with 100% coverage.
- [x] Run pytest coverage + ruff.
- [x] Save Engram summary.

## Decisions
- Sidecar first, no Hermes core patch in this loop.
- New filesystem state lives under `AuditContext.context_dir` (`~/.hermes/context` by default).
- Checkpoint mode never promotes to USER.md/MEMORY.md automatically.
- FTS is SQLite local, OpenViking optional later.
