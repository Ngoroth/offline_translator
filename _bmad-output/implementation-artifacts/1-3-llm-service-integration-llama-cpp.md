# Story 1.3: LLM Service Integration (Llama.cpp)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Developer,
I want to implement the Translation service using Llama.cpp,
So that I can translate transcribed text from one language to another with context awareness.

## Acceptance Criteria

1. **Model Configuration**: Successfully load a GGUF model using the path defined in `config.yaml`.
2. **Translation Engine**: Implement `LLMService.translate(text: str, source_lang: str, target_lang: str) -> str`.
3. **Context Awareness**: The service must inject a system prompt defining the translator persona (e.g., "You are a professional interpreter...").
4. **Concurrency**: Ensure translation inference runs in a separate thread using `asyncio.to_thread` to prevent blocking the main event loop.
5. **Offline Operation**: The service must run entirely offline without any external API calls.
6. **Error Handling**: Implement typed exceptions (`LLMError`, `LLMModelLoadError`) for failure scenarios, integrated with `loguru`.
7. **Type Safety**: The implementation must pass strict `basedpyright` checks (no `Any` types allowed in src).

## Tasks / Subtasks

- [x] Update `LLMSettings` in `src/app/core/config.py`
  - [x] Add `model_path` (validated as .gguf file)
  - [x] Add `context_window` (default 2048)
  - [x] Add `n_threads` (default to CPU count or optimized value)
- [x] Implement `LLMService` in `src/app/services/llm.py`
  - [x] Initialize `Llama` model in `__init__` (offload to thread if slow, or just ensure thread-safety)
  - [x] Implement `translate` method with `asyncio.to_thread` wrapper around `model.create_chat_completion` or `model.__call__`
  - [x] Construct proper prompt structure (ChatML or model-specific format via `llama-cpp-python` chat interface)
  - [x] Add structured logging
- [x] Create unit tests in `tests/unit/test_llm.py`
  - [x] Mock `llama_cpp.Llama` class
  - [x] Test initialization and configuration loading
  - [x] Test `translate` method with mocked responses
  - [x] Test error handling
- [x] Verify `pyproject.toml` dependencies (ensure `llama-cpp-python` is correctly installed)

## Dev Notes

### Critical Implementation Guardrails

- **Async & Threading**: `llama-cpp-python` release the GIL for inference, but the Python call itself blocks the thread until completion. **You MUST use `asyncio.to_thread`** for the actual inference call (`model.create_chat_completion`).
- **Strict Typing**: The project enforces **strict** type checking in `src`.
  - `reportAny = "error"` is active. You cannot use `Any` or un-typed libraries directly without casting or stubs.
  - If `llama_cpp` type stubs are missing/incomplete, you may need to use `typing.cast` or creating a localized stub, but try to use the library's types first if available.
- **Model Lifecycle**: Load the model **once** at service initialization. Do not reload per request.
- **Prompt Engineering**: Use the `create_chat_completion` API if possible for easier system prompt injection.
  - System Prompt: "You are a helpful simultaneous interpreter. Translate the user input directly. Do not add explanations."

### Project Structure Notes

- **Service Location**: `src/app/services/llm.py`
- **Config Location**: `src/app/core/config.py` (extend `Settings` or `LLMSettings`)
- **Testing**: `tests/unit/test_llm.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Services]

## Dev Agent Record

### Agent Model Used

Gemini 3 Pro

### Git Intelligence Summary

- **Recent Changes**: Strict type checking was recently enforced (`ab60afe`). This means you must be very careful with type hints.
- **Previous Story**: `STTService` (Story 1.2) established the pattern of `asyncio.to_thread` and custom Exception classes. Follow this pattern.

### Latest Technical Information

- **Library**: `llama-cpp-python` >= 0.3.2
- **Integration**: Use the high-level `Llama` class.
- **Chat Format**: Prefer `model.create_chat_completion(messages=[...])` to handle system prompts cleanly without manually formatting strings (unless using a raw completion model, in which case use a verified prompt template).

### File List

- src/app/core/config.py (Modified)
- src/app/services/llm.py (New)
- tests/unit/test_llm.py (New)
- tests/unit/test_llm_settings.py (New)
- tests/integration/test_pipeline.py (Modified)
- tests/unit/test_settings.py (Modified)
- src/app/services/translator.py (Deleted)
- tests/unit/test_translator.py (Deleted)
- src/app/settings.py (Deleted)

### Change Log

- Implemented `LLMService` with async translation support.
- Updated `LLMSettings` in `config.py` with `context_window` and `n_threads` fields and `.gguf` validation.
- Added unit tests for LLM service and settings.
- Updated pipeline integration tests to use new settings and fixed `STTService` instantiation in tests.
- Removed legacy `TranslatorService` and migrated integration tests to `LLMService`.

### Completion Notes
All tasks completed. Full test suite passed. Implemented `LLMService` using `llama-cpp-python` with `asyncio.to_thread` for non-blocking inference. Enforced strict typing.
