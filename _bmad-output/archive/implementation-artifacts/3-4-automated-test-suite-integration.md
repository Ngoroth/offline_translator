# Story 3.4: Automated Test Suite Integration

Status: ready-for-dev

## Story

As a Developer,
I want to run a single command to verify the entire system,
So that I can be confident my changes didn't break the translation pipeline.

## Acceptance Criteria

1.  **Given** I have the repository cloned
2.  **When** I run `uv run pytest`
3.  **Then** It should execute all unit, integration, and smoke tests
4.  **And** Tests relying on specific hardware (GPIO) should be skipped gracefully on Windows if mocks aren't forced
5.  **And** A coverage report should be generated (optional but good practice)

## Tasks / Subtasks

- [ ] **Consolidate Test Markers**
    - [ ] Ensure `pyproject.toml` has markers for `gpio`, `slow`, `requires_model`.
    - [ ] Decorate GPIO tests with `@pytest.mark.gpio`.

- [ ] **CI Pipeline Hardening**
    - [ ] Create `scripts/test_all.sh` (or `test_all.bat` for Windows) that runs:
        1. `ruff check .`
        2. `basedpyright`
        3. `pytest`
    - [ ] Ensure this script returns exit code 0 only if ALL pass.

- [ ] **Documentation**
    - [ ] Update `README.md` with "How to Run Tests" section.

## Dev Notes

### Note
This story is mostly "done" thanks to the work in Epic 2 (Story 2.5), but we need to formally wrap it up and ensure the new GPIO tests from 3.1 are integrated correctly.

### References

-   `tests/` directory
-   `pyproject.toml`
