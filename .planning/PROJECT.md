# Offline Translator - Cross-Platform Deployment

## What This Is

Offline speech-to-speech translator running on Windows PC (development) and Raspberry Pi 4 (production). Supports dual speakers with bidirectional translation via PTT buttons. Uses local AI models (Whisper, Qwen, Piper) for fully offline operation.

## Core Value

Run the same codebase on both platforms without manual config changes — one command to launch, one command to deploy.

## Requirements

### Validated

- ✓ Profile-based configuration (config.yaml with desktop_rtx4070 / rpi_deployment)
- ✓ Platform-specific input handlers (keyboard on Windows, evdev/GPIO on Pi)
- ✓ Hardware abstraction layer for PTT input (BaseInput factory)
- ✓ Audio device resolution with fallbacks
- ✓ Different model sizes per platform (small LLM on desktop, tiny on Pi)

### Active

- [ ] CLI flag `--profile` to select config profile without editing config.yaml
- [ ] Deploy script: rsync files to pi@translator + run `uv sync` remotely

### Out of Scope

- Auto-detection of platform (explicit flag is simpler and more predictable)
- Systemd service restart after deploy (user manages service manually)
- GUI for configuration (YAML is sufficient)

## Context

**Current workflow problem:** Switching between Windows dev and Pi deployment requires manually editing `current_profile` in config.yaml. Deploy to Pi requires manual rsync commands.

**Existing infrastructure:**
- Pi accessible via SSH at `pi@translator`
- systemd service manages the translator on Pi (optional restart)
- Models stored in `models/` directory (~1-2GB total)

**Exclusions for sync:**
- `.venv/` — recreated on Pi via `uv sync`
- `__pycache__/` — compiled cache, not needed
- `.git/` — repo history not needed on Pi
- `logs/` — local logs, keep separate

## Constraints

- **Tech Stack**: Python 3.12, uv, pydantic — must maintain compatibility
- **Cross-Platform**: Code must run on Windows (dev) and Linux/RPi (production)
- **Network**: SSH access to Pi required for deploy script

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| `--profile` flag instead of auto-detect | Explicit is simpler, easier to debug, no surprises | — Pending |
| rsync + uv sync instead of git pull | Faster incremental deploys, handles models well | — Pending |
| Exclude .venv from sync | Virtual envs are platform-specific | — Pending |

---
*Last updated: 2026-02-20 after initialization*
