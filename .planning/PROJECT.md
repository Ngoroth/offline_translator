# Offline Translator (Neuromancer Pi)

## What This Is

High-performance, privacy-first speech-to-speech translation system for real-time bilingual communication without internet. Uses an async pipeline architecture for near-zero latency translation, with hardware abstraction for Windows desktop and Raspberry Pi 4 deployment.

## Core Value

Users can have natural bilingual conversations with ≤1.0s latency, entirely offline.

## Requirements

### Validated

- ✓ Async pipeline (STT → LLM → TTS) with concurrent processing — existing
- ✓ PTT input handling (Keyboard, Evdev; GPIO available but not used on target) — existing
- ✓ Barge-in interruption support — existing
- ✓ Hardware Abstraction Layer for cross-platform support — existing
- ✓ Configuration system with profile-based settings — existing
- ✓ Auto-segmentation with VAD pause detection — existing
- ✓ Dual speaker support (Space/Alt keys for different language pairs) — existing
- ✓ Session-based state management with cancellation — existing
- ✓ Verify all tests pass (unit, integration, e2e) — v1.0
- ✓ Verify code works on target device (Windows dev, RPi production via Evdev) — v1.0
- ✓ Dynamic audio device discovery and fallback — v1.0
- ✓ Model file and audio device startup validation — v1.0

### Active

- [ ] Fix GPIO active_low hardcoding (low priority - GPIO not used on target device)
- [ ] Implement system resource (RAM/CPU) constraint checks
- [ ] Add configuration validation at startup
- [ ] Execute thermal stress testing
- [ ] Echo/passthrough mode for audio chain validation
- [ ] Auditory feedback cues for system state

### Out of Scope

- Real-time chat — High complexity, not core value
- Mobile app (Android/iOS) — Phase 3 vision
- Web-based configuration UI — Phase 3 vision
- Multiple concurrent language pairs — Phase 3 vision
- Cloud fallback — Breaks privacy promise
- Auto-update models — Breaks offline guarantee

## Context

### Project State
- Codebase is mature with comprehensive test coverage (142 tests passing)
- v1.0 milestone achieved: dependencies updated, audio auto-discovery implemented, startup verification added.
- Shipped RPi deployment verification with numpad PTT.
- Known technical debt: resource checks deferred, model loading validation missing, GPIO active_low ignored.
- Type checking: 0 errors, 5 warnings (acceptable)
- Linting: All checks pass

### Known Issues (from codebase analysis)
- GPIO active-low hardcoding needs configuration (low priority - GPIO not used on target device)
- Legacy input settings marked for removal
- TTS sample rate assumption (single rate per session)
- Missing: Audio device auto-discovery, echo mode, auditory feedback

### Target Platforms
- **Development:** Windows with USB keyboard PTT
- **Production:** Raspberry Pi 4 with USB numpad (PTT via evdev)

## Constraints

- **Tech Stack:** Python 3.12, uv package manager, no changes
- **AI Models:** Quantized GGUF/ONNX for offline inference
- **Audio:** 16kHz mono float32 standard
- **Privacy:** Zero telemetry, all data on-device
- **Latency:** ≤1.0s from PTT release to audio playback

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Async pipeline with queues | Enables concurrent STT/LLM/TTS processing | ✓ Good |
| Hardware Abstraction Layer | Cross-platform support (Windows/RPi) | ✓ Good |
| Pydantic configuration | Type-safe settings with validation | ✓ Good |
| `StartupVerifier` checks | Fast failure for missing models/audio | ✓ Good |
| Dynamic audio device discovery | Eliminates index hardcoding, adds named fallback | ✓ Good |
| Hardcoded GPIO `active_low` | Temporarily bypassed config for speed | ⚠️ Revisit |
| Deferred model load validation | Checked file existence but deferred RAM/loading | ⚠️ Revisit |

---
*Last updated: 2026-02-21 after v1.0 milestone*