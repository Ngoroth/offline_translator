# Phase 2: Deploy to Pi - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Provide a one-command deployment path (`uv run scripts/deploy.py`) that syncs the codebase to `pi@translator`, excludes non-deployment files, runs dependency installation on the Pi, and reports progress plus clear success/failure outcomes.

</domain>

<decisions>
## Implementation Decisions

### Device readiness baseline
- Required precondition is minimal setup: Raspberry Pi must be reachable over SSH as `pi@translator`.
- Deploy flow should not require full manual pre-provisioning beyond SSH reachability.

### Setup guidance and preflight behavior
- Onboarding/setup documentation format is left to Claude's discretion.
- Preflight checks before sync are left to Claude's discretion.

### Failure message style
- When preflight fails, errors should be concise and actionable: one clear cause plus 1-2 concrete next-step commands.

### Claude's Discretion
- Exact onboarding document format and depth.
- Exact set of preflight checks prior to file sync.

</decisions>

<specifics>
## Specific Ideas

- User emphasized discussion about what must be prepared on the device before deployment.

</specifics>

<deferred>
## Deferred Ideas

- Raspberry Pi OS selection and installation workflow (captured for a separate phase/backlog item).
- Broader device-level configuration guide may warrant a separate discussion/phase if it expands beyond deployment preconditions.

</deferred>

---

*Phase: 02-deploy-to-pi*
*Context gathered: 2026-02-21*
