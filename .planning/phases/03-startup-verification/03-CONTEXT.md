# Phase 3: Startup Verification - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

System validates all prerequisites before user interaction begins. Minimal checks only — models exist and audio devices are available.

</domain>

<decisions>
## Implementation Decisions

### Checks scope
- Only two checks: models exist, audio devices available
- No USB numpad detection (device uses USB numpad, not GPIO)
- No resource threshold checks (RAM/CPU)
- No config validation

### Missing models behavior
- Halt startup immediately
- Print expected model paths to console
- Exit with error code

### Missing audio device behavior
- Halt startup immediately
- Print list of available audio devices
- Exit with error code

### Output format
- Plain text (no colors, no JSON)
- Human-readable but simple

### Logging
- Console only, no log files

### Claude's Discretion
- Exact error message wording
- Exit codes (non-zero for errors)
- Order of checks

</decisions>

<specifics>
## Specific Ideas

- User wants minimal validation — let the app crash naturally for other issues
- USB numpad instead of GPIO for PTT input (no validation needed)

</specifics>

<deferred>
## Deferred Ideas

- GPIO support removed from scope — USB numpad is the input device
- Resource threshold warnings — not needed for this phase

</deferred>

---

*Phase: 03-startup-verification*
*Context gathered: 2026-02-18*
