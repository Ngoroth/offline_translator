# Story 1.1: Core Infrastructure & HAL Skeleton

Status: done

## Story

As a Developer,
I want to establish the project structure, configuration system, and hardware abstraction layer (HAL),
so that I can capture audio and input events on Windows without hardcoding platform dependencies.

## Acceptance Criteria

1. **Project Structure Initialization**: Create the complete directory structure as defined in the Architecture document (`src/app/core`, `src/app/services`, `src/app/orchestrator`, etc.).
2. **Configuration System**: Implement `ConfigService` using `pydantic-settings` to load and strictly validate `config.yaml`.
   - Must validate presence of keys like `input_device_id`, `sample_rate`.
   - Must fail startup if config is invalid.
3. **Hardware Abstraction Layer (HAL)**: Implement `BaseInput` abstract base class in `src/app/core/input.py`.
4. **Windows Input Implementation**: Implement `KeyboardInput` (inheriting `BaseInput`) using `pynput`.
   - Must detect 'Space' and 'Alt' keys (or configured keys).
   - Must NOT block the main asyncio loop (run in thread or use non-blocking listener).
5. **Audio Recorder**: Implement `AudioRecorder` in `src/app/core/audio/recorder.py` using `sounddevice`.
   - Must capture 16kHz mono float32 audio.
   - Must provide an interface to read audio chunks asynchronously.
6. **Logging Setup**: Configure `loguru` in `src/app/core/logging.py`.
   - Output to console and file (`logs/app.log`).
   - JSON format for file logs.
7. **Entry Point**: Create `src/app/main.py` that initializes these services and keeps the application running (even if doing nothing else yet).
8. **Dependency Management**: Add `pydantic-settings`, `pynput`, `sounddevice`, `numpy`, `loguru` to `pyproject.toml` via `uv`.

## Tasks / Subtasks

- [x] **Project Setup**
  - [x] Initialize `pyproject.toml` with `uv`.
  - [x] Create folder structure.
  - [x] Add `ruff` and `basedpyright` configuration.
- [x] **Configuration Module**
  - [x] Define `Settings` class in `src/app/core/config.py`.
  - [x] Create default `config.yaml`.
  - [x] Implement loader.
- [x] **Logging Module**
  - [x] Configure `loguru` sinks in `src/app/core/logging.py`.
- [x] **HAL Input Module**
  - [x] Define `BaseInput` protocol/abstract class.
  - [x] Implement `KeyboardInput` with `pynput` Listener.
  - [x] Expose async event mechanism (press/release queues).
- [x] **Audio Module**
  - [x] Implement `AudioRecorder` class with async streaming.
  - [x] Setup `sounddevice` InputStream with correct parameters (16kHz, mono, float32).
- [x] **Main Application**
  - [x] Wire everything together in `src/app/main.py` using HAL factory.
  - [x] Verify startup logs.

## Dev Notes

- **Architecture Compliance**:
  - **Strict Separation**: `pynput` is isolated in `src/app/core/input.py`.
  - **Async First**: Replaced busy-waiting with `wait_for_release` async event. `AudioRecorder` uses `asyncio.Queue` for streaming.
  - **Type Safety**: Improved Pydantic models with strict validation and better typing.

- **Testing**:
  - Created robust `MockInput` and `MockAudioRecorder` for integration testing.
  - Verified all 24 project tests pass.

### Project Structure Notes

- **Root**: `C:\Projects\offline_translator`
- **Source**: `src/app`
- **Config**: `config.yaml` in root.
- **Logs**: `logs/` directory (gitignored).

### References

- [Architecture: Project Structure](docs/architecture.md#complete-project-directory-structure)
- [Architecture: Hardware Abstraction](docs/architecture.md#hardware-abstraction)
- [PRD: FR18, FR19](docs/prd.md#functional-requirements)

## Dev Agent Record

### Agent Model Used

Antigravity (OpenCode)

### Debug Log References

- Fixed async loop issue in KeyboardInput tests.
- Resolved type errors in pydantic-settings implementation.
- Refactored HAL to be fully asynchronous and platform-agnostic.

### Completion Notes List

- Initialized project structure and dependencies.
- Implemented robust configuration loading with profile support using `pydantic-settings`.
- Set up fully asynchronous HAL for keyboard input with press/release events.
- Implemented audio recording with async streaming support for VAD.
- Configured structured logging (Loguru) with early initialization.
- Created main entry point with HAL factory and clean lifecycle.
- Verified 24 tests passing including new async unit tests.

### File List

- `src/app/main.py` (Refactored)
- `src/app/core/config.py` (Refactored)
- `src/app/core/logging.py` (New)
- `src/app/core/input.py` (Refactored)
- `src/app/core/audio/recorder.py` (Refactored)
- `src/app/core/audio/player.py` (New)
- `src/app/core/audio/__init__.py` (New)
- `tests/unit/test_audio.py` (Updated)
- `tests/unit/test_input.py` (Updated)
- `tests/unit/test_settings.py` (Verified)
- `tests/mocks/mock_input.py` (New)
- `tests/mocks/mock_audio.py` (New)
- `src/app/settings.py` (Deleted)
- `src/app/core/input_windows.py` (Deleted)
- `pyproject.toml` (Modified)


## Change Log

- 2026-01-23: Initial implementation of Core Infrastructure and HAL Skeleton.
- 2026-01-23: Refactored configuration to use `pydantic-settings` and moved to `app.core`.
- 2026-01-23: Unified input implementation and added async support.
