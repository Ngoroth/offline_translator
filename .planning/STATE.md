# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Run the same codebase on both platforms without manual config changes
**Current focus:** Phase 2 - Deploy to Pi

## Current Position

Current Phase: 01.2 of 3 (Investigate VAD-triggered playback timing)
Current Plan: 2
Total Plans in Phase: 2
Status: In Progress
Last activity: 2026-02-22 - Completed 01.2-01-PLAN.md

Progress: [########--] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 2 min
- Total execution time: 0.1 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 2 | 5 min | 2 min |
| 1.1 | 1 | 4 min | 4 min |

**Recent Trend:**
- Last 5 plans: 1 min, 4 min, 4 min
- Trend: Stable

*Updated after each plan completion*
| Phase 01 P01 | 1 min | 3 tasks | 2 files |
| Phase 01 P02 | 4 min | 3 tasks | 2 files |
| Phase 01.1 P01 | 4 min | 3 tasks | 6 files |
| Phase 01.2 P01 | 14 min | 3 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 01]: Implemented profile_override precedence in load_settings() with exact-match validation
- [Phase 01]: Invalid profile errors now include sorted available profile names for correction UX
- [Phase 01]: Added parse_cli_args + cli wrapper to keep --profile handoff testable and isolated from runtime services.
- [Phase 01]: Standardized startup exit codes (0 success, 1 fatal error, 130 interrupt) so invalid profile launches fail non-zero.
- [Phase 01.1]: Recorder backend selection now keys on settings.platform with host fallback used only for platform auto.
- [Phase 01.1]: Sounddevice startup/runtime failures are wrapped in AudioDeviceError to preserve backend-specific guidance.
- [Phase 01.2]: Playback is deferred in player worker while LISTENING unless audio.playback_during_recording is enabled.
- [Phase 01.2]: PTT release remains the unlock point and queued chunks flush in FIFO order.

### Roadmap Evolution

- Phase 01.1 inserted after Phase 1: Fix Windows audio backend selection for desktop profile (URGENT)
- Phase 01.2 inserted after Phase 1: Investigate VAD-triggered translation playback before PTT release during speech pauses (URGENT)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-22
Stopped at: Completed 01.2-01-PLAN.md
Resume file: None
