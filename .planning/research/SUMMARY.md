# Project Research Summary

**Project:** Offline Translator (Neuromancer Pi)
**Domain:** Offline Speech-to-Speech Translation
**Researched:** 2026-02-18
**Confidence:** HIGH

## Executive Summary

This is a **brownfield project** with an existing async pipeline architecture for offline speech-to-speech translation. The system uses faster-whisper for STT, llama.cpp for translation, and Piper for TTS, running in a producer-consumer pattern with cooperative cancellation and hardware abstraction layers for cross-platform support (Windows dev, Raspberry Pi production).

The recommended approach focuses on **verification and reliability** for deployment readiness rather than new features. The architecture is sound with good patterns already in place (sentinel shutdown, session-based cancellation, HAL for inputs). Key priorities are: (1) updating outdated dependencies, (2) implementing audio device auto-discovery for RPi robustness, and (3) adding comprehensive startup verification to catch deployment issues early.

Primary risks center on Raspberry Pi deployment: thermal throttling under sustained AI inference, ALSA device index fragility after reboots, and GPIO input configuration mismatches. All are addressable with proper verification tooling and configuration patterns. The existing codebase has good foundations—this is a hardening and deployment preparation effort.

## Key Findings

### Recommended Stack

Core stack is established and working. Several packages need updates to current versions. Python 3.12 is required due to ML library compatibility constraints (3.13/3.14 not supported by onnxruntime, faster-whisper).

**Core technologies:**
- **faster-whisper 1.2.1**: STT using CTranslate2 — 4x faster than OpenAI Whisper, int8 quantization, Silero-VAD V6 (current, no update needed)
- **llama-cpp-python 0.3.16**: LLM translation — CPU-optimized for RPi, improved memory management (**update from 0.3.8**)
- **piper-tts 1.4.1**: Neural TTS — fast, edge-optimized, improved phonemization (**update from 1.3.0**)
- **sounddevice 0.5.5**: Audio I/O — cross-platform PortAudio, WASAPI improvements (**minor update**)
- **pytest-asyncio 1.3.0**: Async test support — pytest 9 support, drops Python 3.9 (**major update from 0.23.0**)
- **uv**: Package manager — 10-100x faster than pip, Astral's recommended tool

**Platform-specific inputs:**
- Windows: `pynput` for keyboard PTT
- Linux headless: `evdev` for USB devices
- Raspberry Pi: `lgpio` for GPIO buttons

### Expected Features

**Must have (table stakes - P1):**
- **Model Verification at Startup** — Check files exist, load successfully, produce expected outputs
- **Audio Device Auto-Discovery** — USB indices change after reboot; critical for RPi deployment
- **Clear Error Messages** — Specific errors for missing models, no audio device, config errors
- **Graceful Error Recovery** — Pipeline survives STT/LLM/TTS failures (NFR6 already tested)
- **Hardware Compatibility Check** — CPU/memory/audio validation before running

**Should have (differentiators - P2):**
- **Echo/Passthrough Mode** — Audio-in → Audio-out for hardware validation without AI models
- **Diagnostic Script** — Unified troubleshooting tool for deployment issues
- **Auditory Feedback Cues** — Beep patterns for system state, hands-free awareness
- **Model Warmup on Startup** — Eliminates cold-start latency surprise

**Defer (v2+):**
- Translation Quality Indicators — Complex, requires additional quality estimation model
- Latency Dashboard — Nice for debugging, not essential
- Cross-Platform Config Migration — Convenience, not core value

**Anti-features (avoid):**
- Auto-update models — Breaks offline guarantee
- Cloud fallback — Breaks privacy promise
- Real-time everything — Complex race conditions, debugging nightmares

### Architecture Approach

Existing architecture uses async producer-consumer pipeline with workers consuming from asyncio.Queue. Sentinel values signal graceful termination. Session-based cooperative cancellation uses asyncio.Event that workers check. Hardware Abstraction Layer (BaseInput ABC) isolates platform differences.

**Major components:**
1. **Orchestrator** — Main event loop, PTT state machine, barge-in coordination
2. **TranslationPipeline** — Worker task management, queue coordination, session lifecycle
3. **Workers (VAD/STT/LLM/TTS/Player)** — Pipeline stages, each with queue input
4. **SessionManager** — Session ID tracking, validation, cancellation events
5. **Hardware Abstraction Layer** — BaseInput ABC with KeyboardInput/EvdevInput/GPIOInput implementations

**Key patterns:**
- Producer-Consumer with sentinel shutdown
- Cooperative cancellation with asyncio.Event
- Hardware Abstraction Layer for cross-platform
- Session-context injection for model abort on barge-in

### Critical Pitfalls

1. **Thermal Throttling on RPi** — CPU hits 80°C+ under sustained AI inference, latency balloons from 300ms to 2s+. *Prevention: Active cooling (heatsink + fan), thermal monitoring during stress tests.*
2. **ALSA Device Index Fragility** — USB mic index changes after reboot, causing "device not found". *Prevention: Use ALSA device names (`plughw:1,0`) instead of numeric indices, add auto-discovery.*
3. **GPIO Active-Low Hardcoding** — Button triggers on release instead of press due to pull-up resistor wiring. *Prevention: Make `active_low` configurable (already is), document wiring expectations.*
4. **Cross-Platform Input Mismatch** — pynput fails headless, lgpio not on Windows. *Prevention: Use `input_mode` config with platform detection and graceful fallbacks.*
5. **VAD Exception Swallowing** — Current code catches all exceptions silently, masking configuration errors. *Prevention: Replace silent catch with proper logging, add VAD health check.*

## Implications for Roadmap

Based on combined research, suggested phase structure:

### Phase 1: Dependency Updates
**Rationale:** Updates first to catch any breaking changes before adding features; ensures test tooling is current.
**Delivers:** Updated package versions, verified test suite passes.
**Addresses:** STACK.md version updates (llama-cpp-python, piper-tts, pytest-asyncio, ruff, basedpyright)
**Risk:** Minor API changes in updated packages; run full test suite to catch.

### Phase 2: Audio Device Auto-Discovery
**Rationale:** Highest-priority table stake for RPi deployment; directly addresses Pitfall #2 (ALSA index fragility).
**Delivers:** Automatic audio device detection that survives reboots and device reorderings.
**Addresses:** FEATURES.md P1 table stake, PITFALLS.md ALSA device index fragility
**Uses:** sounddevice, ALSA naming conventions
**Avoids:** "Works on my machine" deployment failures

### Phase 3: Startup Verification Suite
**Rationale:** Catches deployment issues before user interaction; combines model verification, error messages, and hardware checks.
**Delivers:** Comprehensive startup checks with clear, actionable error messages.
**Addresses:** FEATURES.md P1 (model verification, clear errors, hardware check)
**Components:** Model file checks, audio device validation, config validation, resource checks

### Phase 4: Diagnostic & Echo Mode
**Rationale:** Troubleshooting tooling for deployment issues; echo mode provides hardware validation path without loading heavy AI models.
**Delivers:** Unified diagnostic script and echo/passthrough mode for audio chain validation.
**Addresses:** FEATURES.md P2 differentiators
**Uses:** Existing AudioRecorder/Player without model loading

### Phase 5: On-Device Deployment Verification
**Rationale:** Final validation on actual Raspberry Pi hardware; addresses all critical pitfalls that only manifest on target platform.
**Delivers:** Verified RPi deployment with thermal monitoring, GPIO testing, and sustained load tests.
**Addresses:** All PITFALLS.md critical items
**Requires:** Physical Pi 5 with active cooling, USB audio, GPIO button

### Phase Ordering Rationale

- **Phase 1 first:** Dependency updates are foundational; breaking changes easier to catch with unchanged codebase
- **Phase 2 before 3:** Audio discovery is highest-impact reliability fix; verification suite can then test it
- **Phase 3 before 4:** Core verification takes priority over convenience features
- **Phase 5 last:** Hardware-specific pitfalls only testable on target device; software changes complete first

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Audio Discovery):** ALSA device naming conventions vary; may need platform-specific research for robust discovery
- **Phase 5 (Deployment):** RPi-specific thermal monitoring approaches; may need `/gsd-research-phase` for monitoring tooling

Phases with standard patterns (skip research-phase):
- **Phase 1 (Updates):** Standard package update process, well-documented
- **Phase 3 (Verification):** Standard startup check patterns, existing code has examples
- **Phase 4 (Diagnostic):** CLI diagnostic patterns well-established

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official docs + PyPI verified; brownfield project with working dependencies |
| Features | HIGH | Multiple industry sources; Google ML production guides; clear MVP definition |
| Architecture | HIGH | Existing codebase analyzed; asyncio patterns well-documented; pytest-asyncio docs |
| Pitfalls | HIGH | Adafruit/RPi guides; existing codebase TODOs confirm issues; concrete prevention strategies |

**Overall confidence:** HIGH

### Gaps to Address

- **GPIO button hardware specifics:** Physical button circuit not specified; may need schematic review during deployment phase. Handle by documenting expected wiring in README.
- **ALSA device naming variations:** Different USB audio devices may have different naming patterns. Handle by testing with target hardware during Phase 5.
- **Thermal thresholds:** Exact Pi 5 throttling behavior under this specific workload unknown. Handle by stress testing during Phase 5 with temperature monitoring.

## Sources

### Primary (HIGH confidence)
- **faster-whisper GitHub** — Version verification, capabilities
- **llama-cpp-python Releases** — Version verification, Gemma 3 support
- **piper-tts PyPI** — Version verification, ARM compatibility
- **pytest-asyncio docs** — Configuration patterns, asyncio_mode
- **Python asyncio docs** — Queue patterns, Event patterns, to_thread
- **Adafruit RPi AI Guide** — RPi deployment patterns, thermal considerations
- **Adafruit USB Audio Guide** — ALSA configuration, device enumeration

### Secondary (MEDIUM confidence)
- **Google ML Production Systems** — Production readiness checklist
- **Edge Impulse Test Guide** — Edge device verification strategies
- **Raspberry Pi Audio Troubleshooting** — Common ALSA issues
- **GPIO Debouncing Guide** — Contact bounce handling

### Tertiary (Context)
- **Existing codebase** — `src/app/`, `tests/` — Architecture patterns, existing implementations, TODO items
- **Home Assistant Asyncio Guide** — Thread safety patterns

---
*Research completed: 2026-02-18*
*Ready for roadmap: yes*
