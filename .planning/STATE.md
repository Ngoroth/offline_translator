# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-20)

**Core value:** Run the same codebase on both platforms without manual config changes
**Current focus:** Phase 2 - Deploy to Pi

## Current Position

Current Phase: 2 of 3 (Deploy to Pi)
Current Plan: 1
Total Plans in Phase: 1
Status: Phase Complete
Last activity: 2026-02-22 - Completed 02-01-PLAN.md

Progress: [##########] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 5
- Average duration: 5 min
- Total execution time: 0.4 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 2 | 5 min | 2 min |
| 1.1 | 1 | 4 min | 4 min |
| 1.2 | 2 | 16 min | 8 min |

**Recent Trend:**
- Last 5 plans: 1 min, 4 min, 4 min, 14 min, 2 min
- Trend: Stable

*Updated after each plan completion*
| Phase 01 P01 | 1 min | 3 tasks | 2 files |
| Phase 01 P02 | 4 min | 3 tasks | 2 files |
| Phase 01.1 P01 | 4 min | 3 tasks | 6 files |
| Phase 01.2 P01 | 14 min | 3 tasks | 3 files |
| Phase 01.2 P02 | 2 min | 3 tasks | 3 files |
| Phase 02 P01 | 3 min | 3 tasks | 3 files |

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
- [Phase 01.2]: Use --playback-during-recording/--no-playback-during-recording with default None so unset CLI preserves profile defaults.
- [Phase 01.2]: Apply playback override only to in-memory settings after load_settings and never persist it to config.yaml.
- [Phase 02]: Canonical deploy target path fixed to /home/pi/offline_translator for rsync and remote uv sync.
- [Phase 02]: Deploy preflight fails fast when remote uv is missing and prints install plus verification guidance.

### Roadmap Evolution

- Phase 01.1 inserted after Phase 1: Fix Windows audio backend selection for desktop profile (URGENT)
- Phase 01.2 inserted after Phase 1: Investigate VAD-triggered translation playback before PTT release during speech pauses (URGENT)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-22
Stopped at: Completed 02-01-PLAN.md
Resume file: None
