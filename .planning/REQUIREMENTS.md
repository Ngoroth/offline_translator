# Requirements: Offline Translator

**Defined:** 2026-02-18
**Core Value:** Users can have natural bilingual conversations with ≤1.0s latency, entirely offline.

## v1 Requirements

Requirements for verification and deployment readiness milestone. Each maps to roadmap phases.

### Dependencies

- [ ] **DEPS-01**: llama-cpp-python updated to 0.3.16
- [ ] **DEPS-02**: piper-tts updated to 1.4.1
- [ ] **DEPS-03**: pytest-asyncio updated to 1.3.0
- [ ] **DEPS-04**: All tests pass after dependency updates

### Audio Device

- [ ] **AUDIO-01**: System can discover audio devices by name (not just index)
- [ ] **AUDIO-02**: System can auto-discover default input/output devices
- [ ] **AUDIO-03**: System handles device disconnection gracefully with clear error message
- [ ] **AUDIO-04**: Configuration supports device name strings (e.g., `plughw:1,0`)

### Verification

- [ ] **VERF-01**: System validates model files exist at startup
- [ ] **VERF-02**: System validates model files load successfully
- [ ] **VERF-03**: System provides clear error messages for missing models
- [ ] **VERF-04**: System checks audio device availability at startup
- [ ] **VERF-05**: System validates configuration at startup
- [ ] **VERF-06**: System checks minimum resources (RAM, CPU) before running

### Error Handling

- [ ] **ERRO-01**: VAD errors are logged (not silently swallowed)
- [ ] **ERRO-02**: Pipeline errors include actionable context
- [ ] **ERRO-03**: GPIO active_low configuration is actually used (fix hardcoding)

### Deployment

- [ ] **DEPL-01**: System runs thermal stress test (10-minute sustained load)
- [ ] **DEPL-02**: System validates GPIO button input on target hardware
- [ ] **DEPL-03**: System validates audio I/O on target hardware

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Diagnostics

- **DIAG-01**: Echo/passthrough mode for audio chain validation without models
- **DIAG-02**: Unified diagnostic script for deployment troubleshooting
- **DIAG-03**: Auditory feedback cues for system state (startup, listening, error)

### Quality

- **QUAL-01**: Translation quality indicators
- **QUAL-02**: Model warmup on startup to eliminate cold-start latency
- **QUAL-03**: Latency dashboard for debugging

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Auto-update models | Breaks offline guarantee |
| Cloud fallback | Breaks privacy promise |
| Real-time everything | Complex race conditions |
| Mobile app (Android/iOS) | Phase 3 vision |
| Web-based configuration UI | Phase 3 vision |
| Multiple concurrent language pairs | Phase 3 vision |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DEPS-01 | Phase 1 | Pending |
| DEPS-02 | Phase 1 | Pending |
| DEPS-03 | Phase 1 | Pending |
| DEPS-04 | Phase 1 | Pending |
| AUDIO-01 | Phase 2 | Pending |
| AUDIO-02 | Phase 2 | Pending |
| AUDIO-03 | Phase 2 | Pending |
| AUDIO-04 | Phase 2 | Pending |
| VERF-01 | Phase 3 | Pending |
| VERF-02 | Phase 3 | Pending |
| VERF-03 | Phase 3 | Pending |
| VERF-04 | Phase 3 | Pending |
| VERF-05 | Phase 3 | Pending |
| VERF-06 | Phase 3 | Pending |
| ERRO-01 | Phase 3 | Pending |
| ERRO-02 | Phase 3 | Pending |
| ERRO-03 | Phase 3 | Pending |
| DEPL-01 | Phase 4 | Pending |
| DEPL-02 | Phase 4 | Pending |
| DEPL-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-18*
*Last updated: 2026-02-18 after initial definition*
