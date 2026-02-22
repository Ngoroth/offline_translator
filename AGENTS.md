# AGENTS.md

This file provides guidance for AI coding agents working in this repository.

## Global Mandates

- **Zero Lint/Type Issues**: You MUST fix all issues reported by `ruff` and `basedpyright`.
- **No Ignores**: You are STRICTLY FORBIDDEN from adding `# noqa`, `# type: ignore`, or any other lint/type suppression comments.
- **Test Integrity**: You are STRICTLY FORBIDDEN from deleting or disabling existing tests. Fix the code or the tests instead.
- **Proactiveness**: If you see a linting or typing issue, fix it immediately as part of your task.

## Knowledge Freshness

**Your training data is outdated** (approximately August 2025). The current date is available
in the environment context (`Today's date` field).

- **Always fetch current documentation** for libraries, APIs, and tools.
- **Python 3.12** is used instead of 3.14 due to ML library compatibility (onnxruntime, faster-whisper).

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12.x | Runtime |
| uv | Package manager |
| ruff | Linter and formatter |
| basedpyright | Type checker |
| pytest | Testing framework |

## Quick Commands

### Environment Setup
```bash
uv sync --extra dev                  # Install all dependencies
uv run python scripts/download_models.py # Download required AI models
```

### Running
```bash
uv run python src/app/main.py        # Run the translator
```

### Testing
```bash
uv run pytest                        # Run all tests
```

### Validation
```bash
uv run basedpyright                  # Mandatory type check
uv run ruff check .                  # Mandatory lint check
```

## Hardware & Cross-Platform Notes
- **Windows**: Development platform, uses `pynput` for keyboard PTT.
- **Raspberry Pi 4 (2GB RAM)**: Target platform with USB mic, USB numpad (PTT via evdev), and speakers.
  - SSH: `ssh pi@translator`
- **Audio**: Standard 16kHz mono float32 for pipeline consistency.

## GSD Workflow Gotchas

- **Do not run** `gsd-tools.cjs commit --help` in this repo workflow.
- The helper can create an actual commit with message `--help` instead of only printing usage.
- Always run commits in the explicit form:
  - `node ./.opencode/get-shit-done/bin/gsd-tools.cjs commit "<message>" --files "<path1>" "<path2>"`
- If commit behavior is unclear, stop and inspect existing workflow docs first rather than probing commit flags.
