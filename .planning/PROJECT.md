# Offline Translator - Cross-Platform Deployment

## What This Is

Offline speech-to-speech translator running on Windows PC (development) and Raspberry Pi 4 (production). Supports dual speakers with bidirectional translation via PTT buttons. Uses local AI models (Whisper, Qwen, Piper) for fully offline operation.

## Core Value

Run the same codebase on both platforms without manual config changes — one command to launch, one command to deploy.

## Current State

Shipped **v1.0 Cross-Platform Deployment** on 2026-02-22.

Delivered in v1.0:
- CLI profile selection (`--profile`) with strict validation and non-persistent runtime override behavior
- Profile-intent recorder backend routing (`settings.platform`) with Windows sounddevice path and Pi/Linux ALSA preservation
- Playback timing controls for hold-to-talk sessions with runtime opt-in for early playback
- One-command deploy workflow (`uv run scripts/deploy.py`) with preflight checks, rsync exclusions, remote `uv sync`, and actionable failures

## Next Milestone Goals

- Parameterize deploy host/path to reduce environment coupling.
- Add post-deploy runtime smoke checks on target hardware.
- Close remaining human-needed verification for real-device playback behavior.

## Requirements

### Validated

- ✓ Profile-based configuration (config.yaml with desktop_rtx4070 / rpi_deployment)
- ✓ Platform-specific input handlers (keyboard on Windows, evdev/GPIO on Pi)
- ✓ Hardware abstraction layer for PTT input (BaseInput factory)
- ✓ Audio device resolution with fallbacks
- ✓ Different model sizes per platform (small LLM on desktop, tiny on Pi)
- ✓ CLI profile flag and startup override behavior (`CLI-01`, `CLI-02`, `CLI-03`) — v1.0
- ✓ Audio backend selection by profile intent (`AUDIO-01`, `AUDIO-02`, `AUDIO-03`) — v1.0
- ✓ Playback timing gate and runtime override semantics (`VAD-GATE-01`, `VAD-GATE-02`, `VAD-GATE-03`) — v1.0
- ✓ One-command deploy workflow (`DEPLOY-01` through `DEPLOY-05`) — v1.0

### Active

- [ ] Deploy target configurability (host/path flags or profile-driven deploy target)
- [ ] Post-deploy smoke verification pipeline for runtime startup checks
- [ ] Complete deferred hardware confirmation checks for playback behavior

### Out of Scope

- Auto-detection of platform (explicit flag is simpler and more predictable)
- Systemd service restart after deploy (user manages service manually)
- GUI for configuration (YAML is sufficient)

## Context

**Current workflow baseline:** Cross-platform switching and deployment are now automated through CLI profile selection and deploy orchestration.

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
| `--profile` flag instead of auto-detect | Explicit is simpler, easier to debug, no surprises | ✓ Good |
| rsync + uv sync instead of git pull | Faster incremental deploys, handles models well | ✓ Good |
| Exclude `.venv` from sync | Virtual environments are platform-specific | ✓ Good |
| Recorder backend selected from `settings.platform` | Profile intent must win over host assumptions | ✓ Good |
| Runtime playback mode override is non-persistent | Launch-time flexibility without config drift | ✓ Good |

---
*Last updated: 2026-02-22 after v1.0 milestone completion*
