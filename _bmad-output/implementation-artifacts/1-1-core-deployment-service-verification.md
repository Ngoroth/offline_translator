# Story 1.1: Core Deployment & Service Verification

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Developer,
I want to deploy and verify the application on Raspberry Pi 4,
so that I can confirm the core pipeline works on the target hardware.

## Acceptance Criteria

1.  **Given** A fresh Raspberry Pi 4 installation (Raspberry Pi OS Bookworm)
    **When** I clone the repository and run `uv sync`
    **Then** All dependencies should install successfully (including `faster-whisper`, `llama-cpp-python`, `piper-tts`, `sounddevice`, `loguru`, `pydantic-settings`).
2.  **When** I run `uv run python src/app/main.py`
    **Then** The application should start without crashing.
3.  **And** The application should initialize the service container and logging system.
4.  **And** If models or audio devices are missing/unconfigured, the system should LOG a warning but NOT crash (graceful degradation for initial verification).
5.  **And** The application should handle a graceful shutdown via `Ctrl+C`.

## Tasks / Subtasks

- [ ] Initialize Project Structure
  - [ ] Create `pyproject.toml` with `uv` dependencies (Python 3.12).
  - [ ] Create directory structure as per Architecture (`src/app`, `src/app/core`, `src/app/services`, `src/app/orchestrator`).
- [ ] Implement Core Infrastructure
  - [ ] Create `src/app/core/config.py` using `pydantic-settings` (define `Settings` class).
  - [ ] Create `src/app/core/logging.py` using `loguru` (configure sinks/levels).
  - [ ] Create `src/app/main.py` entry point (asyncio loop, service initialization).
- [ ] Implement Service Skeletons (Interfaces only)
  - [ ] Create abstract base classes / protocols for `STT`, `LLM`, `TTS` services.
  - [ ] Implement concrete "Stub" or "Real" classes that initialize (but may do nothing or log warning if models missing).
- [ ] Verify Deployment on RPi 4 (Simulated/Actual)
  - [ ] Ensure `uv sync` works on ARM64 (check for wheel availability or compilation requirements).
  - [ ] Verify startup logs.

## Dev Notes

- **Architecture Compliance**:
    - Follow strict directory structure from `architecture.md`.
    - Use `asyncio` for the main loop.
    - DO NOT implement full logic for STT/LLM/TTS yet - just the class structure and initialization.
    - DO NOT implement full HAL/GPIO yet - focus on the application shell.

- **Dependency Management (`uv`)**:
    - This is the first story, so `pyproject.toml` needs to be created.
    - Critical dependencies: `fastapi` (if needed for API, otherwise `typer` or just `asyncio`), `pydantic-settings`, `loguru`, `sounddevice`, `numpy`, `faster-whisper`, `llama-cpp-python`, `piper-tts` (or python wrapper).
    - **Note on RPi**: `llama-cpp-python` might need `CMAKE_ARGS="-DGGML_BLAS=ON -DGGML_OPENBLAS=ON"` for best performance, but for this story, just installing it is enough.

- **Error Handling**:
    - The `main.py` must catch `KeyboardInterrupt` for graceful shutdown.
    - Service initialization failures (e.g., missing model file) should be caught and logged as WARNING, allowing the app to stay up (as per AC).

### Project Structure Notes

- Alignment with `architecture.md` is mandatory.
- Root: `src/app/main.py`.

### References

- [Architecture: Project Structure](_bmad-output/planning-artifacts/architecture.md#complete-project-directory-structure)
- [Epics: Story 1.1](_bmad-output/planning-artifacts/epics.md#story-11-core-deployment--service-verification)

## Dev Agent Record

### Agent Model Used

antigravity-gemini-3-pro

### Debug Log References

### Completion Notes List

### File List
