# Requirements: Offline Translator - Cross-Platform Deployment

**Defined:** 2026-02-20
**Core Value:** Run the same codebase on both platforms without manual config changes

## v1 Requirements

### CLI Configuration

- [x] **CLI-01**: User can specify profile via `--profile <name>` flag when launching the app
- [x] **CLI-02**: Flag overrides `current_profile` in config.yaml without modifying the file
- [x] **CLI-03**: Error message shown if specified profile does not exist in config.yaml

### Deployment

- [x] **DEPLOY-01**: User can run `uv run scripts/deploy.py` to sync codebase to Raspberry Pi
- [x] **DEPLOY-02**: Deploy script excludes `.venv/`, `__pycache__/`, `.git/`, `logs/` from sync
- [x] **DEPLOY-03**: Deploy script runs `uv sync` on Pi after file sync completes
- [x] **DEPLOY-04**: Deploy script connects to Pi via SSH at `pi@translator`
- [x] **DEPLOY-05**: Deploy script shows progress/success/failure status

### Audio Backend Selection

- [x] **AUDIO-01**: Recorder backend selection uses active profile/runtime platform intent (`settings.platform`) as source of truth
- [x] **AUDIO-02**: `desktop_rtx4070` startup uses a Windows-compatible sounddevice/PortAudio recorder path and avoids Linux-only `arecord` dependency
- [x] **AUDIO-03**: `rpi_deployment` startup preserves existing ALSA/`arecord` recorder behavior and actionable backend-specific startup errors

### VAD Playback Timing Gate

- [x] **VAD-GATE-01**: `audio.playback_during_recording` controls whether translated playback can start before PTT release
- [x] **VAD-GATE-02**: Existing playback mode remains configurable via profile config and per-launch CLI override without persisting runtime overrides to `config.yaml`
- [x] **VAD-GATE-03**: Existing VAD pause timing and queued chunk FIFO release behavior remain unchanged while applying playback gate

## v2 Requirements

(Deferred — none identified)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-detect platform | Explicit flag is simpler, no magic |
| Systemd restart after deploy | User manages service manually |
| Incremental model sync | Full sync is simpler, models rarely change |
| GUI configuration | YAML is sufficient for this project |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 1 | Complete |
| CLI-02 | Phase 1 | Complete |
| CLI-03 | Phase 1 | Complete |
| DEPLOY-01 | Phase 2 | Complete |
| DEPLOY-02 | Phase 2 | Complete |
| DEPLOY-03 | Phase 2 | Complete |
| DEPLOY-04 | Phase 2 | Complete |
| DEPLOY-05 | Phase 2 | Complete |
| AUDIO-01 | Phase 01.1 | Complete |
| AUDIO-02 | Phase 01.1 | Complete |
| AUDIO-03 | Phase 01.1 | Complete |
| VAD-GATE-01 | Phase 01.2 | Complete |
| VAD-GATE-02 | Phase 01.2 | Complete |
| VAD-GATE-03 | Phase 01.2 | Complete |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-20*
*Last updated: 2026-02-22 after Phase 01.2 Plan 02 execution*
