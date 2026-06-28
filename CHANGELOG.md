# Changelog

## 0.5.0

- Added file-backed Error Bank extraction for fixed compiler/runtime/test failures.
- Added MiMo-style controlled context rebuild sidecar:
  - `checkpoint --session <id>` writes 11-section session checkpoints.
  - `rebuild --session <id>` emits budgeted `CONTROLLED CONTEXT REBUILD` packets.
  - `fts-index` / `fts-search` provide local SQLite FTS5 recall over `~/.hermes/context/**/*.md`.
- Hardened checkpoint extraction against compaction summaries, preserved task-list injections, and tool-rich historical blobs.
- Kept product coverage at 100% with wheel/build/twine gates.

## 0.4.0

- Rebranded to `self-ershov-memory`.
- Removed legacy staged-memory public surface.
- Kept one product CLI: `self-ershov-memory`.
- Required 100% coverage for the product package `self_ershov_memory`.
