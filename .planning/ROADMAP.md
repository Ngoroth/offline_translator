# Roadmap: Offline Translator - Cross-Platform Deployment

## Overview

Enable seamless switching between development (Windows) and production (Raspberry Pi) environments through CLI profile selection and one-command deployment. This milestone delivers the core value: run the same codebase on both platforms without manual config changes.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: CLI Profile Flag** - Add `--profile` flag to select config without editing files (completed 2026-02-21)
- [x] **Phase 01.1: Fix Windows audio backend selection for desktop profile** - Ensure `desktop_rtx4070` uses Windows recorder backend while `rpi_deployment` keeps ALSA `arecord` (completed 2026-02-21)
- [x] **Phase 01.2: Investigate VAD-triggered translation playback before PTT release during speech pauses** - Gate early playback while keeping speaker mode default-off and headset mode opt-in (completed 2026-02-22)
- [x] **Phase 2: Deploy to Pi** - One-command deployment to Raspberry Pi via rsync (completed 2026-02-22)

## Phase Details

### Phase 1: CLI Profile Flag
**Goal**: User can select configuration profile via command-line flag, eliminating manual config.yaml edits when switching platforms.
**Depends on**: Nothing (first phase)
**Requirements**: CLI-01, CLI-02, CLI-03
**Success Criteria** (what must be TRUE):
  1. User can launch app with `--profile desktop_rtx4070` and app loads that profile's settings
  2. User can launch app with `--profile rpi_deployment` and app loads that profile's settings
  3. If user specifies a profile that doesn't exist in config.yaml, clear error message is shown
  4. Profile flag takes precedence over `current_profile` in config.yaml without modifying the file
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md - Add profile override resolution/validation in config loader with tests
- [x] 01-02-PLAN.md - Add CLI --profile parsing and main entrypoint wiring with tests

### Phase 01.2: Investigate VAD-triggered translation playback before PTT release during speech pauses (INSERTED)

**Goal:** [Urgent work - to be planned]
**Depends on:** Phase 1
**Plans:** 2/2 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 01.2 to break down) (completed 2026-02-22)

### Phase 01.1: Fix Windows audio backend selection for desktop profile (INSERTED)

**Goal:** Desktop profile startup selects a Windows-compatible recorder backend from active profile settings so Windows launches do not execute Linux-only `arecord`, while Raspberry Pi profile behavior remains unchanged.
**Depends on:** Phase 1
**Requirements:** AUDIO-01, AUDIO-02, AUDIO-03
**Success Criteria** (what must be TRUE):
  1. Launching with `--profile desktop_rtx4070` uses a sounddevice/PortAudio recorder path and does not fail with `arecord command not found`
  2. Launching with `--profile rpi_deployment` still routes recorder startup through existing ALSA/`arecord` behavior
  3. Recorder backend selection is driven by active profile intent (`settings.platform`) rather than host OS-only detection
  4. Recorder startup failures preserve actionable backend-specific guidance via existing audio error UX
**Plans:** 1/1 plans complete

Plans:
- [x] 01.1-01-PLAN.md - Add profile-driven recorder backend selector, wire main startup path, and extend tests

### Phase 2: Deploy to Pi
**Goal**: User can deploy the entire codebase to Raspberry Pi with a single command, enabling rapid iteration cycles.
**Depends on**: Nothing (independent of CLI flag functionality)
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05
**Success Criteria** (what must be TRUE):
  1. User runs `uv run scripts/deploy.py` and code syncs to `pi@translator`
  2. Unnecessary files (`.venv/`, `__pycache__/`, `.git/`, `logs/`) are excluded from sync
  3. After file sync completes, `uv sync` runs automatically on Pi to install dependencies
  4. Script displays progress during sync and clear success/failure status at completion
  5. SSH connection errors are reported with actionable guidance
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md - Implement staged `scripts/deploy.py` orchestration with rsync excludes, remote `uv sync`, tests, and deploy usage docs

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 01.1 → 01.2 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. CLI Profile Flag | 2/2 | Complete    | 2026-02-21 |
| 1.1. Windows Audio Backend Selection | 1/1 | Complete | 2026-02-21 |
| 1.2. VAD Playback Timing Gate | 2/2 | Complete | 2026-02-22 |
| 2. Deploy to Pi | 1/1 | Complete | 2026-02-22 |
