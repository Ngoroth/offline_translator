# Requirements: Offline Translator - Cross-Platform Deployment

**Defined:** 2026-02-20
**Core Value:** Run the same codebase on both platforms without manual config changes

## v1 Requirements

### CLI Configuration

- [x] **CLI-01**: User can specify profile via `--profile <name>` flag when launching the app
- [x] **CLI-02**: Flag overrides `current_profile` in config.yaml without modifying the file
- [x] **CLI-03**: Error message shown if specified profile does not exist in config.yaml

### Deployment

- [ ] **DEPLOY-01**: User can run `uv run scripts/deploy.py` to sync codebase to Raspberry Pi
- [ ] **DEPLOY-02**: Deploy script excludes `.venv/`, `__pycache__/`, `.git/`, `logs/` from sync
- [ ] **DEPLOY-03**: Deploy script runs `uv sync` on Pi after file sync completes
- [ ] **DEPLOY-04**: Deploy script connects to Pi via SSH at `pi@translator`
- [ ] **DEPLOY-05**: Deploy script shows progress/success/failure status

## v2 Requirements

(Deferred — none identified)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-detect platform | Explicit flag is simpler, no magic |
| Systemd restart after deploy | User manages service manually |
| Incremental model sync | Full sync is simpler, models rarely change |
| GUI configuration | YAML is sufficient for this project |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 1 | Complete |
| CLI-02 | Phase 1 | Complete |
| CLI-03 | Phase 1 | Complete |
| DEPLOY-01 | Phase 2 | Pending |
| DEPLOY-02 | Phase 2 | Pending |
| DEPLOY-03 | Phase 2 | Pending |
| DEPLOY-04 | Phase 2 | Pending |
| DEPLOY-05 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-20*
*Last updated: 2026-02-20 after initial definition*
