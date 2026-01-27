# Project Documentation Index

## Project Overview

- **Type:** Monolith
- **Primary Language:** Python 3.12
- **Architecture:** Async Pipeline with HAL

## Quick Reference

### Tech Stack
- **Runtime:** Python 3.12+
- **STT:** faster-whisper (>= 1.2.1)
- **LLM:** llama-cpp-python (>= 0.3.2)
- **TTS:** piper-tts (>= 1.3.0)
- **Audio:** sounddevice, numpy
- **VAD:** webrtcvad-wheels

### Entry Point
`src/app/main.py` - Run with: `uv run python src/app/main.py`

### Architecture Pattern
Async Pipeline with Hardware Abstraction Layer (HAL) - concurrent processing of STT, LLM, and TTS stages

## Generated Documentation

- [Project Overview](./project-overview.md)
- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
- [API Contracts](./api-contracts.md) _(To be generated)_
- [Data Models](./data-models.md) _(To be generated)_
- [Component Inventory](./component-inventory.md) _(To be generated)_
- [Deployment Guide](./deployment-guide.md) _(To be generated)_

## Existing Documentation

- [README.md](../README.md) - Project overview, features, and getting started
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Async pipeline and HAL design details
- [SCENARIOS.md](../SCENARIOS.md) - Interaction patterns (Barge-in, Multi-phrase)
- [AGENTS.md](../AGENTS.md) - AI coding agent guidance and coding standards

## Getting Started

### Prerequisites
- Python 3.12+
- C++ Build Tools (for llama-cpp-python)
- uv package manager

### Installation
```bash
uv sync --extra dev
```

### Download AI Models
```bash
uv run python scripts/download_models.py
```

### Run the Application
```bash
uv run python src/app/main.py
```

### Controls
- **Speaker A (Space):** English → Russian
- **Speaker B (Alt):** Russian → English
- **Hold** to speak, **Release** to hear translation
- Press anytime to interrupt (barge-in)

### Testing
```bash
uv run pytest
```

## Configuration

The application uses `config.yaml` with multiple profiles:
- **desktop_rtx4070**: Windows development with GPU acceleration
- **rpi_deployment**: Raspberry Pi production (CPU only)

See [Development Guide](./development-guide.md#configuration-profiles) for details.

## Project Type Notes

This is a **CLI application with hardware interfaces**. The project type (CLI) has the following documentation characteristics:

- **API Contracts:** Not applicable (no REST/GraphQL API)
- **Data Models:** No database schema (uses in-memory audio/text buffers)
- **Component Inventory:** Not applicable (UI components are for web/mobile projects)
- **Deployment Guide:** Not found (no Dockerfile, docker-compose, or CI/CD detected)

For comprehensive documentation of the async pipeline architecture, see [Architecture.md](./architecture.md).
