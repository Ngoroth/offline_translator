# Story 3.3: Structured Logging & Diagnostics

Status: ready-for-dev

## Story

As a Support Engineer,
I want detailed logs written to a file,
So that I can diagnose why the system failed in the field where there is no screen.

## Acceptance Criteria

1.  **Given** The system is running in headless mode
2.  **When** An error occurs (e.g., model crash) or state changes
3.  **Then** It should be logged to `logs/app.log`
4.  **And** The log format should include timestamp, severity, module, and message
5.  **And** Log rotation should be enabled (e.g., 10MB limit, keep 5 files) to prevent disk fill-up
6.  **And** Startup configuration (without sensitive data) should be logged at INFO level

## Tasks / Subtasks

- [ ] **Configure Loguru**
    - [ ] Modify `src/app/core/logging.py`:
        - [ ] Add file sink: `logs/app_{time}.log` or `logs/latest.log`.
        - [ ] Configure rotation: "10 MB" or "00:00" (daily).
        - [ ] Configure compression: "zip".
        - [ ] Set level based on config (DEBUG/INFO).

- [ ] **Add Contextual Logging**
    - [ ] Update `src/app/main.py` to log startup config dump (sanitize keys if any).
    - [ ] Update `src/app/orchestrator/pipeline.py` to log session state transitions with `session_id`.
    - [ ] Update `src/app/services/*` to log model load stats (RAM usage, load time).

- [ ] **Diagnostics Utility**
    - [ ] Create simple script `scripts/diagnose.py` that parses the last log file and prints "Errors: X, Warnings: Y" summary.

## Dev Notes

### Architecture & Tech Stack

-   **Loguru**: Already in use. Just need to configure the file sink properly.
-   **Rotation**: Essential for embedded devices with limited SD card space.

### References

-   `src/app/core/logging.py`
