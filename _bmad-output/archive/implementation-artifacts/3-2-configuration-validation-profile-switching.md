# Story 3.2: Configuration Validation & Profile Switching

Status: ready-for-dev

## Story

As a User,
I want the system to check my configuration and model paths at startup,
So that I don't discover a missing file halfway through a conversation.

## Acceptance Criteria

1.  **Given** A `config.yaml` file with invalid model paths
2.  **When** I start the application
3.  **Then** It should exit immediately with a clear, human-readable error message (not a stack trace)
4.  **And** It should allow switching between "Desktop" and "Pi" profiles via a single config flag (`current_profile`)
5.  **And** It should validate that `speaker_a_key` and `speaker_b_key` are not identical
6.  **And** It should validate that audio devices (if specified by index) actually exist

## Tasks / Subtasks

- [ ] **Enhance Config Validation Logic**
    - [ ] Modify `src/app/core/config.py`:
        - [ ] Add `model_validator` to `AppSettings` to check existence of all model files (`stt`, `llm`, `tts`, `speakers`).
        - [ ] Add validator to check `speaker_a_key != speaker_b_key`.
    - [ ] Implement `validate_audio_devices` helper using `sounddevice.query_devices()`.

- [ ] **Implement Profile Switching CLI**
    - [ ] (Already partially implemented in 2.4, verify robustness)
    - [ ] Add CLI argument `--profile <name>` to `src/app/main.py` that overrides `current_profile` in yaml.

- [ ] **User-Friendly Error Handling**
    - [ ] Update `src/app/main.py`: Wrap startup logic in `try...except ValidationError`.
    - [ ] Print clean error messages to stderr (e.g., "Error: LLM model file not found at '...'") before exiting.

- [ ] **Testing**
    - [ ] `tests/unit/test_config_validation.py`:
        - [ ] Test missing files -> Error.
        - [ ] Test duplicate keys -> Error.
        - [ ] Test valid config -> Success.

## Dev Notes

### Architecture & Tech Stack

-   **Pydantic**: Use `@model_validator(mode='after')` for cross-field validation.
-   **CLI**: Use `sys.argv` or `argparse` in `main.py` for the profile override.

### References

-   `src/app/core/config.py`
-   `src/app/main.py`
