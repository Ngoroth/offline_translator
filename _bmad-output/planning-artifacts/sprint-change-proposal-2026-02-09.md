# Sprint Change Proposal: Developer Experience & Hardware Tooling

**Date:** 2026-02-09
**Proposer:** BMAD Agent (on behalf of User)
**Trigger:** Slow feedback loop during Raspberry Pi hardware integration.

## 1. Issue Summary
**Problem:** The current "Big Bang" testing approach requires deploying and running the full application (60s+ startup) to test low-level hardware components (Audio, Input, GPIO). This results in a slow, frustrating debug cycle where errors are often masked by system complexity.

**Context:** Discovered during Epic 3 execution. "Blind" runs of the full stack led to significant time wastage debugging basic audio driver issues (sample rates, buffer sizes).

## 2. Impact Analysis
*   **Epics:** Epic 3 (Configuration) is blocked by hardware instability. Epic 4 is needed to unblock it.
*   **PRD/MVP:** No impact on core requirements. MVP remains the same, but confidence in delivery increases.
*   **Architecture:** Requires formal definition of a "Hardware Test Layer" (isolated from AI services).

## 3. Recommended Approach
**Strategy:** "Divide and Conquer" via Tooling.
**Action:** Introduce **Epic 4: Developer Experience & Tooling**.
**Rationale:** By isolating hardware verification into fast (<5s) independent scripts, we can iterate rapidly on the Raspberry Pi without waiting for the full stack to load.

## 4. Detailed Change Proposals

### New Epic: Epic 4 - Developer Experience & Hardware Tooling
**Goal:** Reduce hardware feedback loop from minutes to seconds.

**Story 4.1: Remote Deployment & Test Runner**
*   **Goal:** `scripts/deploy_and_test.sh` to sync code and run specific tests on Pi in one command.
*   **Success:** <10s turnaround time for code change -> test result.

**Story 4.2: Component Isolation Runners**
*   **Goal:** Standalone scripts (`run_component.py`) for Audio, Input, VAD.
*   **Success:** Verify microphone works in isolation before starting the main app.

**Story 4.3: Mock Mode (MOCK_AI=true)**
*   **Goal:** Run the main application logic without loading heavy models.
*   **Success:** Test button flows and state machines on Pi with <3s startup.

## 5. Implementation Handoff
*   **Scope:** Moderate (Add new Epic, no major refactor of existing code).
*   **Owner:** Development Team.
*   **Next Steps:**
    1.  Update `epics.md` with Epic 4.
    2.  Update `sprint-status.yaml`.
    3.  Implement Story 4.1 immediately.
