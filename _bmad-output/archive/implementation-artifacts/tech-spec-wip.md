---
title: 'Raspberry Pi Integration & Stability'
slug: 'rpi-integration'
created: '2026-02-09T00:00:00'
status: 'in-progress'
stepsCompleted: [1]
tech_stack: []
files_to_modify: []
code_patterns: []
test_patterns: []
---

# Tech-Spec: Raspberry Pi Integration & Stability

**Created:** 2026-02-09T00:00:00

## Overview

### Problem Statement

The application works on PC but fails with unspecified errors on the target Raspberry Pi hardware (`translator`). The hardware layer (GPIO) and audio configuration likely need specific implementation for the ARM platform.

### Solution

Establish SSH connectivity to `translator`, diagnose runtime errors, implement missing hardware abstractions (GPIO via `lgpio`/`RPi.GPIO`), and stabilize the audio pipeline for the specific hardware constraints.

### Scope

**In Scope:**
- SSH connectivity and remote debugging on `translator`.
- Diagnosing startup and runtime errors on RPi.
- Implementing `HardwareInput` for Raspberry Pi (GPIO).
- Configuring audio devices for the specific hardware.
- Verifying `faster-whisper` and `llama-cpp-python` performance on RPi 4.

**Out of Scope:**
- Major architectural changes to the core pipeline (unless blocking).
- New feature development unrelated to stability.

## Context for Development

### Codebase Patterns
- `src/app/core/hardware` is the likely location for GPIO implementation.
- `scripts/hardware_check.py` exists but may need updates for RPi.

### Files to Reference
| File | Purpose |
| ---- | ------- |
| `src/app/core/input.py` | Base class for hardware input |
| `src/app/core/input_windows.py` | Windows implementation (reference) |
| `docs/raspberry-pi-setup.md` | Setup instructions |

### Technical Decisions
- Use `lgpio` or `RPi.GPIO` for button handling? (To be determined in investigation).
- Audio device selection via configuration or auto-detection.
