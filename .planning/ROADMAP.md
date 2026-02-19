# Roadmap: Offline Translator (Neuromancer Pi)

## Overview

This roadmap guides the verification and deployment readiness of a mature offline speech-to-speech translation system. The journey moves from dependency foundation → audio reliability → startup validation → hardware deployment, ensuring the system is production-ready on Raspberry Pi with ≤1.0s translation latency.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Dependency Updates** - Update llama-cpp-python, piper-tts, pytest-asyncio with verified compatibility ✓
- [ ] **Phase 2: Audio Device Discovery** - Auto-detect audio devices by name for RPi deployment reliability
- [ ] **Phase 3: Startup Verification** - Comprehensive validation before user interaction begins
- [ ] **Phase 4: Deployment Verification** - Validate on target Raspberry Pi hardware

## Phase Details

### Phase 1: Dependency Updates
**Goal**: Updated dependency foundation with verified compatibility
**Depends on**: Nothing (first phase)
**Requirements**: DEPS-01, DEPS-02, DEPS-03, DEPS-04
**Success Criteria** (what must be TRUE):
  1. All 128 existing tests pass after dependency updates
  2. Pipeline runs without errors with updated packages
  3. No new linting or type checking errors introduced
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md — Update llama-cpp-python, piper-tts, pytest-asyncio with test verification ✓

### Phase 2: Audio Device Discovery
**Goal**: Reliable audio device detection that survives reboots and device changes
**Depends on**: Phase 1
**Requirements**: AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04
**Success Criteria** (what must be TRUE):
  1. User can configure audio devices by name instead of numeric index
  2. System automatically discovers available audio devices on startup
  3. User sees clear error message when audio device is disconnected during runtime
  4. Configuration accepts device name strings (e.g., "plughw:1,0")
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Create device discovery module with list/resolve functions
- [ ] 02-02-PLAN.md — Integrate device resolution with error handling

### Phase 3: Startup Verification
**Goal**: System validates all prerequisites before user interaction begins
**Depends on**: Phase 2
**Requirements**: VERF-01, VERF-02, VERF-03, VERF-04, VERF-05, VERF-06, ERRO-01, ERRO-02, ERRO-03
**Success Criteria** (what must be TRUE):
  1. User sees clear error if model files are missing at startup
  2. User sees clear error if audio device is unavailable at startup
  3. User sees clear error if configuration is invalid
  4. System warns if insufficient RAM or CPU resources
  5. VAD errors appear in logs with actionable context
  6. GPIO active_low configuration actually affects button behavior
**Plans**: TBD

### Phase 4: Deployment Verification
**Goal**: Verified operation on target Raspberry Pi hardware
**Depends on**: Phase 3
**Requirements**: DEPL-01, DEPL-02, DEPL-03
**Success Criteria** (what must be TRUE):
  1. System runs 10-minute sustained translation load without thermal throttling
  2. GPIO button triggers PTT reliably on target hardware
  3. Audio input and output work correctly on target hardware
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Dependency Updates | 1/1 | Complete | 2026-02-18 |
| 2. Audio Device Discovery | 0/TBD | Not started | - |
| 3. Startup Verification | 0/TBD | Not started | - |
| 4. Deployment Verification | 0/TBD | Not started | - |

---
*Roadmap created: 2026-02-18*
*Total requirements: 20 v1 requirements mapped*
