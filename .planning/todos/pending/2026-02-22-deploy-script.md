---
created: 2026-02-22T07:43:46.812Z
title: Refactor deploy path configuration
area: tooling
files:
  - scripts/deploy.py:11
  - scripts/deploy.py:29
  - tests/unit/test_deploy.py:19
---

## Problem

The deploy flow still relies on hardcoded path decisions in `scripts/deploy.py` (notably `REMOTE_DIR` and source path shaping for rsync). This makes the script less portable across environments and harder to evolve when deployment targets change.

## Solution

Move path configuration to a more flexible mechanism (for example CLI flags and/or config-backed defaults) while preserving one-command behavior. Keep strong validation and actionable errors, then update tests to cover configurable paths and Windows/Linux path normalization.
