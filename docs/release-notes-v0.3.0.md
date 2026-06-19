# Hermes Mnemos v0.3.0 Release Notes

Status: approved and shipped as `v0.3.0` on 2026-06-02.

## What changed since v0.2.0

- Added `mnemos inbox` so staged artifacts can be reviewed as a queue, with both text and JSON output.
- Added `mnemos harvest --recent` and wired `create`/`review` to the local session-reader fallback path.
- Surfaced proposal `risk`, `priority`, `reason`, `source_quote`, and `policy_flags` in summarize, digest, report-card, and inbox views.
- Added `digest --inbox` plus the inbox-digest cron mode for stdout-only operator reporting.
- Tightened writeback path policy so memory, user, fact, and skill proposals can only target their approved destination shapes.
- Added source preflight secret checks so provider calls are blocked before source content can leave the local process.
- Preserved existing uppercase `MEMORY.md`/`USER.md` files during apply instead of creating duplicate lowercase files.
- Bumped the plugin version to `0.3.0`.

## Release verdict

This is the first Hermes Mnemos line that treats the inbox as a real operator surface instead of a one-off artifact view.
It is the shipped Mnemos Inbox release.
