# Offline Translator (Neuromancer Pi)

## What This Is

High-performance, privacy-first speech-to-speech translation system for real-time bilingual communication without internet. Uses an async pipeline architecture for near-zero latency translation, with hardware abstraction for Windows desktop and Raspberry Pi 4 deployment.

## Core Value

Users can have natural bilingual conversations with ≤1.0s latency, entirely offline.

## Requirements

### Validated

- ✓ Async pipeline (STT → LLM → TTS) with concurrent processing — existing
- ✓ PTT input handling (Keyboard, Evdev, GPIO) — existing
- ✓ Barge-in interruption support — existing
- ✓ Hardware Abstraction Layer for cross-platform support — existing
- ✓ Configuration system with profile-based settings — existing
- ✓ Auto-segmentation with VAD pause detection — existing
- ✓ Dual speaker support (Space/Alt keys for different language pairs) — existing
- ✓ Session-based state management with cancellation — existing

### Active

- [ ] Verify all tests pass (unit, integration, e2e)
- [ ] Verify code works on target device (Windows dev, RPi production)
- [ ] Fix any critical issues found during verification

### Out of Scope

- Real-time chat — High complexity, not core value
- Mobile app (Android/iOS) — Phase 3 vision
- Web-based configuration UI — Phase 3 vision
- Multiple concurrent language pairs — Phase 3 vision

## Context

### Project State
- Codebase is mature with comprehensive test coverage (128 tests)
- Recently cleaned up old documentation (docs/, _bmad-output/)
- PRD saved to root as prd.md
- Type checking: 0 errors, 4 warnings (acceptable)
- Linting: All checks pass

### Known Issues (from codebase analysis)
- GPIO active-low hardcoding needs configuration
- Legacy input settings marked for removal
- TTS sample rate assumption (single rate per session)
- VAD error handler could be more verbose
- Missing: Audio device auto-discovery, echo mode, auditory feedback

### Target Platforms
- **Development:** Windows with USB keyboard PTT
- **Production:** Raspberry Pi 4 with USB numpad or GPIO buttons

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
| Session-based cancellation | Clean barge-in support | ✓ Good |
| Pydantic configuration | Type-safe settings with validation | ✓ Good |
| loguru for logging | Structured JSON logs with rotation | ✓ Good |

---
*Last updated: 2026-02-18 after initialization*
