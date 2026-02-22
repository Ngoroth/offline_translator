---
phase: 02-deploy-to-pi
verified: 2026-02-22T07:20:36Z
status: human_needed
score: 4/4 must-haves verified
human_verification:
  - test: "Run deploy end-to-end against the actual Raspberry Pi"
    expected: "`uv run scripts/deploy.py` completes preflight, rsync, remote `uv sync`, then prints `[deploy] success`"
    why_human: "Requires live SSH/network/remote host state that cannot be validated from static analysis and unit tests"
  - test: "Validate real SSH failure guidance from operator machine"
    expected: "On connectivity/auth failure, output ends with `[deploy] failed: ...` and includes actionable `ssh pi@translator` remediation"
    why_human: "Real transport/auth failure modes depend on runtime environment and are only partially represented by mocked tests"
---

# Phase 2: Deploy to Pi Verification Report

**Phase Goal:** User can deploy the entire codebase to Raspberry Pi with a single command, enabling rapid iteration cycles.
**Verified:** 2026-02-22T07:20:36Z
**Status:** human_needed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | User runs `uv run scripts/deploy.py` and the project syncs to `pi@translator` without manual copy commands. | ? UNCERTAIN | `scripts/deploy.py` defines staged `main()` flow and `uv run python scripts/deploy.py --help` works; live sync requires real Pi validation (`scripts/deploy.py:120`, `scripts/deploy.py:125`). |
| 2 | Deployment excludes `.venv/`, `__pycache__/`, `.git/`, and `logs/` from transfer output. | ✓ VERIFIED | Excludes are codified and appended into rsync command (`scripts/deploy.py:12`, `scripts/deploy.py:34`); covered by unit test assertions (`tests/unit/test_deploy.py:8`). |
| 3 | After sync, dependencies are installed on Pi automatically via `uv sync` in the deployed directory. | ✓ VERIFIED | Remote command is `ssh pi@translator "cd /home/pi/offline_translator && uv sync"` and stage order is preflight -> rsync -> remote uv sync (`scripts/deploy.py:40`, `scripts/deploy.py:126`, `tests/unit/test_deploy.py:88`). |
| 4 | Deploy output shows stage progress and ends with clear success or concise actionable failure guidance. | ✓ VERIFIED | Stage banners and terminal status lines are explicit (`scripts/deploy.py:44`, `scripts/deploy.py:106`, `scripts/deploy.py:128`, `scripts/deploy.py:131`); failure guidance mapped for SSH/remote-uv cases (`scripts/deploy.py:51`, `scripts/deploy.py:83`, `tests/unit/test_deploy.py:32`). |

**Score:** 4/4 truths verified (1 requires live human validation)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `scripts/deploy.py` | Stage-based deployment orchestration (preflight -> rsync -> remote uv sync) | ✓ VERIFIED | Exists, substantive implementation with command builders and stage runner; executable entrypoint present (`scripts/deploy.py:29`, `scripts/deploy.py:105`, `scripts/deploy.py:135`). |
| `tests/unit/test_deploy.py` | Regression tests for command construction, excludes, stage ordering, and failure mapping | ✓ VERIFIED | Exists with 8 focused tests; `uv run pytest tests/unit/test_deploy.py` passes. |
| `README.md` | Operator instructions for deploy preconditions and command usage | ✓ VERIFIED | "Deploy to Raspberry Pi" section documents preconditions, command, behavior, and output (`README.md:53`). |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `scripts/deploy.py` | `pi@translator` | ssh preflight and remote command execution | ✓ WIRED | Host constant used by SSH reachability, uv probe, and remote sync commands (`scripts/deploy.py:10`, `scripts/deploy.py:73`, `scripts/deploy.py:84`, `scripts/deploy.py:40`). |
| `scripts/deploy.py` | `rsync` | sync command with required excludes and progress | ✓ WIRED | rsync command includes `--progress` and all required excludes via `REQUIRED_EXCLUDES` loop (`scripts/deploy.py:12`, `scripts/deploy.py:32`, `scripts/deploy.py:34`). |
| `scripts/deploy.py` | remote `uv sync` | post-sync SSH command in deploy directory | ✓ WIRED | Remote command composes `cd /home/pi/offline_translator && uv sync` and is run after rsync in `main()` (`scripts/deploy.py:40`, `scripts/deploy.py:125`, `scripts/deploy.py:126`). |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| `DEPLOY-01` | `02-01-PLAN.md` | User can run `uv run scripts/deploy.py` to sync codebase to Raspberry Pi | ? NEEDS HUMAN | Script and CLI path exist (`scripts/deploy.py:120`, `README.md:60`), but real sync requires live Pi execution. |
| `DEPLOY-02` | `02-01-PLAN.md` | Deploy script excludes `.venv/`, `__pycache__/`, `.git/`, `logs/` from sync | ✓ SATISFIED | Exclude tuple + command construction + tests (`scripts/deploy.py:12`, `scripts/deploy.py:34`, `tests/unit/test_deploy.py:8`). |
| `DEPLOY-03` | `02-01-PLAN.md` | Deploy script runs `uv sync` on Pi after file sync completes | ✓ SATISFIED | Remote uv command builder and enforced stage order (`scripts/deploy.py:40`, `scripts/deploy.py:126`, `tests/unit/test_deploy.py:116`). |
| `DEPLOY-04` | `02-01-PLAN.md` | Deploy script connects to Pi via SSH at `pi@translator` | ✓ SATISFIED | `REMOTE_HOST` constant and all SSH commands target `pi@translator` (`scripts/deploy.py:10`, `scripts/deploy.py:73`, `scripts/deploy.py:84`). |
| `DEPLOY-05` | `02-01-PLAN.md` | Deploy script shows progress/success/failure status | ✓ SATISFIED | Stage prints and final success/failure output with actionable guidance (`scripts/deploy.py:44`, `scripts/deploy.py:128`, `scripts/deploy.py:131`). |

Orphaned requirements for Phase 2 in `REQUIREMENTS.md`: none (all Phase 2 IDs are declared in plan frontmatter).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| None | - | No TODO/FIXME/placeholders or empty stub implementations detected in phase key files | - | No blocker/warning anti-patterns identified |

### Human Verification Required

### 1. End-to-end Pi Deploy

**Test:** From a machine with SSH access, run `uv run scripts/deploy.py`.
**Expected:** Output shows `[deploy] preflight...`, `[deploy] rsync...`, `[deploy] remote uv sync...`, and ends with `[deploy] success`.
**Why human:** Requires live SSH/network connectivity and remote host state.

### 2. Real SSH Failure Path

**Test:** Intentionally break connectivity/auth (e.g., temporary wrong host alias or denied key) and run `uv run scripts/deploy.py`.
**Expected:** Script exits non-zero and prints concise actionable remediation including `ssh pi@translator`.
**Why human:** Runtime SSH failure modes depend on real environment conditions.

### Gaps Summary

No code gaps found in must-have artifacts or wiring. Automated verification indicates phase implementation is complete; remaining validation is operational (live Raspberry Pi execution).

---

_Verified: 2026-02-22T07:20:36Z_
_Verifier: Claude (gsd-verifier)_
