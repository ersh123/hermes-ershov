# Live Memory Mutation Architecture Survey

## Direction memo

Don't bolt live `MEMORY.md` / `USER.md` writes onto the current artifact flow. That path (`src/hermes_dreaming/apply.py`) is good for staged proposal files, but it's the wrong seam for durable memory mutation.

The safe seam is a dedicated memory I/O layer plus one mutation tool that owns locking, backups, idempotence, and state updates. Anything else is how you end up with half-written memory and a very smug rollback ticket.

## What the current repo already has

Current repo pieces that matter:

- `src/hermes_dreaming/apply.py` — atomic temp-file writes plus backups for approved artifact proposals
- `src/hermes_dreaming/validation.py` — path safety, duplicate-target checks, secret-like content scanning
- `src/hermes_dreaming/state.py` — run ledger / DREAMS diary state, but only for CLI runs right now
- `src/hermes_dreaming/commands/status.py` — status rendering for artifacts and run ledger stats
- `src/hermes_dreaming/cli.py` — artifact-first command surface (`create`, `diff`, `validate`, `apply`, `discard`, `status`)
- `src/hermes_dreaming/__init__.py` — Hermes plugin registration / CLI bridge

What it does not have yet:

- canonical `MEMORY.md` / `USER.md` path constants
- a dedicated read/preview/write module for those files
- a mutation lock
- a promotion hash / idempotence log
- run-scoped counters for live memory writes
- a status view that speaks in live-mutation terms, not artifact-only terms

## What the upstream comparison repo does

In `/tmp/hermes-dreaming-compare`, the live-memory seam is split cleanly:

- `hermes_dreaming/paths.py` defines the canonical Hermes memory paths, dreaming state root, backups, runs, and sidecars
- `hermes_dreaming/memory_io.py` reads and mutates `MEMORY.md` / `USER.md` with atomic temp-file writes
- `hermes_dreaming/tools/apply_memory_op.py` is the only mutator, and it owns the lock, backup snapshot, idempotence hash, score gates, and state updates
- `hermes_dreaming/sidecar.py` keeps append-only candidate/decision/promotion logs
- `hermes_dreaming/scoring.py` holds the hard thresholds and validation gates
- `hermes_dreaming/state.py` tracks `current_run`, `last_run`, `last_successful_run`, and run summaries
- `hermes_dreaming/commands/status.py` surfaces current-run focus, last error, memory usage, and counts
- `hermes_dreaming/commands/run.py`, `review.py`, `compact.py`, `install_cron.py`, and `orchestration.py` wire the live and dry-run workflows

That upstream split matters. It keeps pure file I/O, policy, and orchestration separated instead of smashing them into one giant apply function.

## Minimum module set for safe live mutation

If we want atomic read/modify/write on `MEMORY.md` and `USER.md` with backups and idempotence, the minimum seam is this:

| Module | Why it has to exist |
|---|---|
| `src/hermes_dreaming/paths.py` | Canonical file locations for `MEMORY.md`, `USER.md`, backups, state, runs, and sidecars. No hardcoded paths scattered through tool code. |
| `src/hermes_dreaming/memory_io.py` | Read/parse/preview/write helpers for the memory files. This is where atomic `os.replace` / temp-file write lives. |
| `src/hermes_dreaming/scoring.py` | Hard gates for what can be written live. If the score is below threshold, the mutator never runs. |
| `src/hermes_dreaming/sidecar.py` | Append-only records for decisions and promotions, plus hash-based dedupe so repeat runs don't double-apply the same thing. |
| `src/hermes_dreaming/state.py` | `current_run`, `last_run`, `last_successful_run`, and run counters, so status and rollback aren't guessing. |
| `src/hermes_dreaming/tools/apply_memory_op.py` | The sole live mutator. It acquires the lock, makes one backup snapshot per run, checks idempotence, applies the write, verifies it, and records the result. |
| `src/hermes_dreaming/commands/status.py` | Visibility into current run, last run, last error, and memory/backups health. You don't want live writes that are invisible. |
| `src/hermes_dreaming/cli.py` | Surface the review/live/status commands cleanly; this is where `run` vs `review` vs `status` gets routed. |
| `src/hermes_dreaming/__init__.py` | If this is Hermes-facing, keep the plugin/command registration here so the live-mutation path is reachable from Hermes itself. |

For tests, the first wave should be:

- `tests/test_memory_io.py`
- `tests/test_apply_memory_op.py`
- `tests/test_status.py`
- `tests/test_run_records.py`
- `tests/test_cli.py`

## Safety hazards to design around

These are the failure modes that matter, not the imaginary ones:

1. Concurrent writers
   - Cron plus a manual CLI run can race.
   - Fix: file lock around the mutation path, not just around state writes.

2. Duplicate replays
   - The same op can be proposed twice across runs.
   - Fix: hash the op signature and record promotion hashes before the next write.

3. Wrong target / path escape
   - A bad `target_path` can walk outside the live root.
   - Fix: normalize to relative paths and reject absolute or parent-traversal paths.

4. Partial success / split-brain state
   - File write succeeds but state or logs don't, or vice versa.
   - Fix: backup first, atomic write second, state/log updates inside the same locked section, and post-write verification.

5. Capacity overflow
   - `MEMORY.md` and `USER.md` are prompt-visible budget files, not dumping grounds.
   - Fix: enforce per-file limits before writing.

6. Secret leakage
   - A live mutation path is the easiest way to accidentally entomb a token or private datum.
   - Fix: scan source/proposal text for secret-like patterns before the write gate.

7. Bad rollback story
   - If the only backup is a vague artifact dump, you're toast when something goes sideways.
   - Fix: per-run backup snapshot of both `MEMORY.md` and `USER.md`, plus a clear restore path and promotion log.

8. Status lies
   - If status only reports artifact counts, the operator can't tell whether live writes are healthy.
   - Fix: status must show current run, last run, failures, and memory usage of the live roots.

## Rollback needs

Rollback has to be deliberate, not aspirational.

Minimum rollback contract:

- one timestamped backup directory per run
- both `MEMORY.md` and `USER.md` copied before the first live mutation
- promotion hash or equivalent idempotence key stored before / with the write
- state record that says which run wrote what
- a status command that can tell you which backup belongs to which run

If a write fails verification after the file is replaced, the mutator should have enough context to restore the backup without guessing.

## Recommended implementation order

1. Add the path constants and memory file I/O layer
   - Create `src/hermes_dreaming/paths.py` and `src/hermes_dreaming/memory_io.py`
   - Add tests first for parse / preview / atomic write / path safety

2. Add scoring and sidecar plumbing
   - Create `src/hermes_dreaming/scoring.py` and `src/hermes_dreaming/sidecar.py`
   - Add tests for threshold rejection and idempotence hashes

3. Add the sole live mutator
   - Create `src/hermes_dreaming/tools/apply_memory_op.py`
   - Make it the only code path that can mutate `MEMORY.md` / `USER.md`
   - Put the lock, backup snapshot, post-write verification, and state updates here

4. Make status tell the truth
   - Extend `src/hermes_dreaming/state.py` and `src/hermes_dreaming/commands/status.py`
   - Surface `current_run`, `last_run`, `last_successful_run`, live file sizes, and any recent error

5. Wire the CLI / Hermes surface
   - Update `src/hermes_dreaming/cli.py`
   - If needed, expose live vs review mode through `src/hermes_dreaming/__init__.py`

6. Only then add automation wrappers
   - `commands/run.py`, `commands/review.py`, `commands/compact.py`, `commands/install_cron.py`
   - Don't let cron or compact become the first place live mutation exists

## Bottom line

The current repo already knows how to stage artifacts safely. It does not yet have the live-memory seam.

The seam we want is:

`memory_io.py` → `apply_memory_op.py` → `state.py` / `sidecar.py` → `status.py`

Everything else is supporting plumbing. If we put live `MEMORY.md` / `USER.md` writes anywhere else, we're just making the blast radius bigger and the rollback story worse.
