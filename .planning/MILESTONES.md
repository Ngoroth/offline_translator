# Milestones

## v1.0 Cross-Platform Deployment (Shipped: 2026-02-22)

**Delivered:** Cross-platform profile switching, platform-intent audio backend routing, playback timing policy controls, and one-command Raspberry Pi deployment.

**Phases completed:** 4 phases, 6 plans, 18 tasks

**Key accomplishments:**
- Added strict `--profile` startup selection with override precedence and invalid-profile fail-fast handling.
- Routed recorder backend selection through `settings.platform` intent (Windows sounddevice vs Linux/RPi ALSA).
- Preserved backend-specific startup guidance while removing desktop `arecord` dependency failures.
- Added VAD playback timing gate and runtime `--playback-during-recording` override without config persistence.
- Delivered `scripts/deploy.py` staged deploy flow (`preflight -> rsync -> remote uv sync`) with exclusions and actionable failures.

**Stats:**
- 41 files changed, 3484 insertions, 39 deletions
- 4 phases, 6 plans, 18 tasks
- 2 days from first milestone commit to final milestone feature commit
- Git range: `6cf32cb` -> `b2ec7ad`

**Known debt accepted at completion:**
- Deploy success remains partially environment-dependent on live `pi@translator` availability.
- Hardware-level playback behavior checks remain documented as human-needed.
- Deploy host/path configurability follow-up remains pending.

---
