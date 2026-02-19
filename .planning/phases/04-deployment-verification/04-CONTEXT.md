# Phase 4: Deployment Verification - Context

**Gathered:** 2026-02-18
**Status:** Ready for execution

<domain>
## Phase Boundary

Validate the translator runs correctly on target Raspberry Pi hardware. This is live verification on the actual device, not automated CI. Tests confirm audio I/O and PTT input work on the Pi.

**Removed from scope:** 10-minute sustained load test (not needed)

</domain>

<decisions>
## Implementation Decisions

### Test Execution Format
- Live session testing: Claude SSHs into Pi and runs tests interactively
- User participates only to press numpad buttons when prompted
- Test order: Pre-flight checks → Audio I/O → Numpad PTT
- Manual checklist approach (not automated script)

### Hardware Configuration
- Target: Pi 4 accessible at `pi@translator`
- PTT via USB numpad using evdev (NOT GPIO)
- Numpad keys: 5 for Speaker A, 6 for Speaker B
- Evdev device: `/dev/input/event1` ("SIGMACHIP USB Keyboard")
- Audio input: `plughw:1,0` (USB microphone)
- Audio output: `plughw:0,0` (built-in or USB speakers)
- Profile: `rpi_deployment`

### Failure Handling
- Abort on failure: stop and report, fix before continuing
- No automatic retry - one attempt per test
- Detailed error output: exact error message, failed command, and fix suggestion

### Results Reporting
- Console output only - no log files created
- Per-test pass/fail status printed as tests run
- Overall summary at the end with pass/fail verdict

### Pre-flight Checks
- Model files: verify STT (tiny), LLM (Qwen3-0.6B-Q4_K_M.gguf), and TTS (both voices) exist
- Audio devices: verify both `plughw:1,0` and `plughw:0,0` are available
- Evdev: verify `/dev/input/event1` exists and is readable by user

### Claude's Discretion
- Exact commands to verify each check
- How to test audio I/O (record sample, play back)
- How to verify numpad input is captured

</decisions>

<specifics>
## Specific Ideas

- "I'll do everything, user just presses buttons when needed"
- Use existing rpi_deployment profile configuration
- SSH connection: `pi@translator`

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 04-deployment-verification*
*Context gathered: 2026-02-18*
