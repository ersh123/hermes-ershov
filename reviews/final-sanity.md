# Final Sanity Report

## Verdict
Ready to ship, with one small housekeeping fix applied during QA: runtime outputs under `.ershov/` are now ignored by git.

## Checks Run
- `pytest -q` → passed
- `python -m build --wheel` → passed
- `PYTHONPATH=src python -m hermes_ershov status --artifact-root /tmp/hermes-ershov-smoke-artifacts` -> passed
- `PYTHONPATH=src python -m hermes_ershov create --live-root <tmp>/live --artifact-root <tmp>/artifacts --source <tmp>/src` -> passed, staged artifact created and validated
- `git check-ignore -v .ershov/artifacts .ershov/backups .ershov/discarded` → passed after the `.gitignore` update

## Issues Found
1. `.ershov/` runtime output root was not ignored by git, which meant a default CLI run could dirty the repo with generated artifacts and backups.
   - Fixed by adding `.ershov/` to `.gitignore`.

## Non-Blocking Notes
- Running the package as `python -m hermes_ershov` from the raw source tree needs `PYTHONPATH=src`; the intended release path is the installed `ershov` console script.

## Ship Readiness
Yes, the repo is in ship-ready shape for the current MVP contract.
