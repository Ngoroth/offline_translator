---
phase: 04-deployment-verification
plan: "01"
subsystem: hardware
tags: [raspberry-pi, audio, evdev, numpad, deployment, verification]

# Dependency graph
requires:
  - phase: 03-startup-verification
    provides: Verified startup process with audio device discovery
provides:
  - Hardware verification pass/fail report for DEPL-02 (numpad PTT) and DEPL-03 (audio I/O)
  - Confirmed Pi system readiness with all peripherals functional
affects: [deployment, production]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SSH-based remote hardware verification
    - ALSA audio device testing with arecord/aplay

key-files:
  created: []
  modified: []

key-decisions:
  - "Audio capture device confirmed at plughw:2,0 (USB mic on card 2), not plughw:1,0 as plan assumed"
  - "Audio playback via plughw:0,0 (bcm2835 Headphones) confirmed working"
  - "Numpad PTT via /dev/input/event1 with evdev confirmed functional for KP_5 and KP_6"

patterns-established:
  - "Hardware verification via SSH remote commands"
  - "Audio test pattern: record 3s sample, verify file size, play back"

requirements-completed: [DEPL-02, DEPL-03]

# Metrics
duration: 9 min
completed: 2026-02-19
---
# Phase 4 Plan 1: Hardware Verification Summary

**Live hardware verification on Raspberry Pi confirmed audio I/O and numpad PTT input functional on target deployment hardware**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-19T08:53:50Z
- **Completed:** 2026-02-19T09:02:34Z
- **Tasks:** 3
- **Files modified:** 0 (verification only)

## Accomplishments
- Verified all model files exist at expected paths (LLM: 396MB, TTS en: 78MB, TTS ru: 63MB)
- Confirmed audio capture via USB mic at plughw:2,0 and playback via Headphones at plughw:0,0
- Verified evdev numpad PTT input for both Speaker A (KP_5) and Speaker B (KP_6) roles

## Task Commits

This plan was verification-only with no code changes. No task commits required.

**Plan metadata:** (pending commit)

## Files Created/Modified
None - verification plan only, no code changes.

## Decisions Made
- Audio device mapping confirmed: USB mic at `plughw:2,0`, headphones at `plughw:0,0`
- Plan assumption of `plughw:1,0` for capture was incorrect; actual device discovery handles this automatically
- Numpad PTT working correctly via evdev on `/dev/input/event1`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Audio device naming discrepancy**
- **Found during:** Task 1 (Pre-flight checks)
- **Issue:** Plan specified `plughw:1,0` for audio capture, but USB PnP Sound Device is on card 2 (`plughw:2,0`). Card 1 is HDMI audio output.
- **Fix:** Used correct device `plughw:2,0` for audio capture testing
- **Files modified:** None (testing adjustment only)
- **Verification:** `arecord -D plughw:2,0` succeeded with 3-second recording
- **Impact:** Audio device discovery in codebase already handles this via dynamic detection

---

**Total deviations:** 1 auto-fixed (1 blocking - device naming)
**Impact on plan:** Minor - the audio device discovery system already handles dynamic naming. No code changes needed.

## Issues Encountered
None - all verification steps passed.

## User Setup Required

**External hardware verification requires physical access.** See [04-USER-SETUP.md](./04-USER-SETUP.md) for:
- Raspberry Pi hardware checklist (power, network, peripherals)
- USB numpad connection for PTT input
- USB microphone and speakers/headphones for audio I/O

## Verification Summary

```
=== DEPLOYMENT VERIFICATION SUMMARY ===

Pre-flight Checks: PASS
  - Model files: OK (3/3 found)
  - Audio devices: OK (capture + playback available)
  - Evdev device: OK (/dev/input/event1 readable)
  - Input group: OK (user in 'input' group)

Audio I/O Test: PASS
  - Recording: OK (3s at 16kHz mono via plughw:2,0)
  - Playback: OK (via plughw:0,0)
  - User verified audible: YES

Numpad PTT Test: PASS
  - KP_5 (Speaker A): DETECTED
  - KP_6 (Speaker B): DETECTED

OVERALL: PASS
```

## Next Phase Readiness
- All hardware verification complete - target system ready for production deployment
- Phase 4 complete - milestone v1.0 deployment readiness achieved

---
*Phase: 04-deployment-verification*
*Completed: 2026-02-19*

## Self-Check: PASSED

- [x] SUMMARY.md created at expected path
- [x] STATE.md updated with position and metrics
- [x] ROADMAP.md updated with plan progress
- [x] Requirements DEPL-02, DEPL-03 marked complete
- [x] Metadata commit: `0c721e2`
