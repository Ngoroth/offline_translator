---
phase: 02-deploy-to-pi
plan: 01
subsystem: infra
tags: [deploy, rsync, ssh, uv, raspberry-pi]
requires:
  - phase: 01.2-vad-playback-timing-gate
    provides: runtime behavior baseline carried into deployment package
provides:
  - One-command deploy pipeline with preflight, rsync sync, and remote uv sync
  - Regression coverage for deploy command construction, stage ordering, and failure guidance
  - Operator documentation for deploy preconditions, usage, and expected output
affects: [release-operations, pi-runtime]
tech-stack:
  added: []
  patterns: [stage-based deployment pipeline, explicit subprocess command arrays]
key-files:
  created: [scripts/deploy.py]
  modified: [tests/unit/test_deploy.py, README.md]
key-decisions:
  - "Canonical remote deploy directory is /home/pi/offline_translator for both rsync and uv sync stages."
  - "Deployment preflight fails fast on missing remote uv with install and verification guidance instead of bootstrap automation."
patterns-established:
  - "Deploy scripts should provide stage banners and one-line final status output."
  - "SSH return code 255 is mapped to actionable connectivity guidance."
requirements-completed: [DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05]
duration: 3 min
completed: 2026-02-22
---

# Phase 2 Plan 1: Deploy to Pi Summary

**One-command Raspberry Pi deployment now runs preflight checks, rsyncs with strict exclusions, and executes remote `uv sync` with concise actionable failure output.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-22T07:12:31Z
- **Completed:** 2026-02-22T07:16:09Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added `scripts/deploy.py` with deterministic `preflight -> rsync -> remote uv sync` orchestration.
- Enforced required rsync exclusions (`.venv/`, `__pycache__/`, `.git/`, `logs/`) plus progress output and canonical trailing-slash path semantics.
- Added deploy regression tests covering command construction, stage order, and failure guidance mapping.
- Added README operator docs for Pi deployment preconditions, command usage, and expected stage output.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement deploy preflight and staged command orchestration** - `6472976` (feat)
2. **Task 2: Add rsync excludes, progress output, and post-sync uv install flow** - `5708723` (feat)
3. **Task 3: Add deploy regression tests and operator usage docs, then run quality gates** - `b2ec7ad` (feat)

Additional plan-scope fix commit:

4. **Rule 1 output-ordering fix discovered during verification** - `060064d` (fix)

## Files Created/Modified
- `scripts/deploy.py` - Deploy pipeline entrypoint with preflight/tool checks, rsync orchestration, and remote `uv sync`.
- `tests/unit/test_deploy.py` - Deterministic deploy regression tests with subprocess mocking and stage-order assertions.
- `README.md` - "Deploy to Raspberry Pi" section with preconditions, command, behavior, and expected output.

## Decisions Made
- Locked one canonical remote directory (`/home/pi/offline_translator`) for sync/install consistency.
- Kept preflight strict: missing `uv` on Pi surfaces direct install + verification steps instead of automatic remote bootstrap.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Flushed stage output to preserve readable ordering on preflight failure**
- **Found during:** Final verification smoke run (`uv run python scripts/deploy.py`)
- **Issue:** stderr failure line could appear before stdout stage banner due buffering, reducing operator clarity.
- **Fix:** Added `flush=True` to stage/preflight/success prints.
- **Files modified:** `scripts/deploy.py`
- **Verification:** Re-ran deploy command and confirmed ordered output; reran pytest, ruff, and basedpyright.
- **Committed in:** `060064d`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Improves operator-facing clarity without expanding scope.

## Issues Encountered
None.

## User Setup Required

External services require manual configuration. See `02-USER-SETUP.md` for SSH environment prerequisites.

## Next Phase Readiness
- Phase complete, ready for transition.
- Deployment command behavior is covered by tests and passes lint/type gates on touched files.

---
*Phase: 02-deploy-to-pi*
*Completed: 2026-02-22*

## Self-Check: PASSED
