# Roadmap: Offline Translator - Cross-Platform Deployment

## Overview

Enable seamless switching between development (Windows) and production (Raspberry Pi) environments through CLI profile selection and one-command deployment. This milestone delivers the core value: run the same codebase on both platforms without manual config changes.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: CLI Profile Flag** - Add `--profile` flag to select config without editing files
- [ ] **Phase 2: Deploy to Pi** - One-command deployment to Raspberry Pi via rsync

## Phase Details

### Phase 1: CLI Profile Flag
**Goal**: User can select configuration profile via command-line flag, eliminating manual config.yaml edits when switching platforms.
**Depends on**: Nothing (first phase)
**Requirements**: CLI-01, CLI-02, CLI-03
**Success Criteria** (what must be TRUE):
  1. User can launch app with `--profile desktop_rtx4070` and app loads that profile's settings
  2. User can launch app with `--profile rpi_deployment` and app loads that profile's settings
  3. If user specifies a profile that doesn't exist in config.yaml, clear error message is shown
  4. Profile flag takes precedence over `current_profile` in config.yaml without modifying the file
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md - Add profile override resolution/validation in config loader with tests
- [ ] 01-02-PLAN.md - Add CLI --profile parsing and main entrypoint wiring with tests

### Phase 2: Deploy to Pi
**Goal**: User can deploy the entire codebase to Raspberry Pi with a single command, enabling rapid iteration cycles.
**Depends on**: Nothing (independent of CLI flag functionality)
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05
**Success Criteria** (what must be TRUE):
  1. User runs `uv run scripts/deploy.py` and code syncs to `pi@translator`
  2. Unnecessary files (`.venv/`, `__pycache__/`, `.git/`, `logs/`) are excluded from sync
  3. After file sync completes, `uv sync` runs automatically on Pi to install dependencies
  4. Script displays progress during sync and clear success/failure status at completion
  5. SSH connection errors are reported with actionable guidance
**Plans**: TBD

Plans:
- [ ] 02-01: [Brief description of first plan]

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. CLI Profile Flag | 1/2 | In Progress | - |
| 2. Deploy to Pi | 0/TBD | Not started | - |
