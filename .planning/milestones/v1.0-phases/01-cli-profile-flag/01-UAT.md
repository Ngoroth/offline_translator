---
status: complete
phase: 01-cli-profile-flag
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md
started: 2026-02-21T08:09:00.790Z
updated: 2026-02-21T08:55:23.147174Z
---

## Current Test

[testing complete]

## Tests

### 1. Launch with explicit desktop profile
expected: When you run the app with `--profile desktop_rtx4070`, startup should continue normally and clearly indicate that `desktop_rtx4070` is the active profile.
result: pass

### 2. Launch with explicit Raspberry Pi profile
expected: When you run the app with `--profile rpi_deployment`, startup should continue normally and clearly indicate that `rpi_deployment` is the active profile.
result: pass

### 3. Invalid profile returns actionable failure
expected: When you run the app with a nonexistent profile (for example `--profile does_not_exist`), startup should fail fast, show a clear error that includes the invalid name, list available profiles, and exit non-zero.
result: pass

### 4. No profile flag uses config default
expected: When you run the app without `--profile`, it should use the profile from `current_profile` in `config.yaml` and start normally.
result: pass

### 5. CLI help documents profile flag
expected: Running `uv run python src/app/main.py --help` should show `--profile` in help output for discoverability.
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

none yet
