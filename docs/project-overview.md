# Offline Translator - Project Overview

## Project Name

**Offline Translator (Neuromancer Pi)**

## Description

High-performance, configurable offline speech-to-speech translator designed for low-latency real-time dialogue. The system features an async pipeline architecture that enables concurrent processing of audio, text, and speech for near-zero latency.

## Executive Summary

The Offline Translator is a privacy-first translation system that runs entirely offline, ensuring no data leaves the device. It supports dual speakers with dedicated PTT (Push-to-Talk) controls and handles barge-in scenarios seamlessly. The architecture is designed with a Hardware Abstraction Layer (HAL) to support multiple platforms, including Windows desktops (keyboard PTT) and Raspberry Pi (GPIO PTT).

## Tech Stack Summary

| Category | Technology | Version |
|----------|-----------|---------|
| **Runtime** | Python | 3.12+ |
| **Package Manager** | uv | Latest |
| **STT** | faster-whisper | >= 1.2.1 |
| **LLM** | llama-cpp-python | >= 0.3.2 |
| **TTS** | piper-tts | >= 1.3.0 |
| **Audio** | sounddevice, numpy | >= 0.5.3, >= 2.4.1 |
| **VAD** | webrtcvad-wheels | >= 2.0.14 |
| **Input** | pynput | >= 1.8.1 |
| **Logging** | loguru | >= 0.7.3 |
| **Config** | pydantic | >= 2.0.0 |
| **Testing** | pytest | >= 7.0 |

## Architecture Type

**Async Pipeline with Hardware Abstraction Layer (HAL)**

The system uses a three-stage async pipeline:
1. **STT**: Speech-to-Text (faster-whisper with VAD)
2. **LLM**: Translation (llama-cpp-python with Qwen/Llama)
3. **TTS**: Text-to-Speech (piper-tts with ONNX)

## Repository Structure

**Type:** Monolith (single cohesive codebase)

## Features

- **Offline First**: All processing (STT, LLM, TTS) happens locally
- **Low Latency**: Async concurrent processing for near-zero latency
- **Dual Speaker Support**: Two PTT keys (Space/Alt) for bilingual dialogue
- **Barge-in**: Interrupt machine at any time by pressing PTT
- **Auto-Segmentation**: Processes speech segments while you hold the button
- **Cross-Platform**: Windows (keyboard) and Raspberry Pi (GPIO) support
- **Privacy Driven**: No data ever leaves the device

## Links to Detailed Documentation

### Generated Documentation
- [Architecture](./architecture.md) - Complete system architecture and design
- [Source Tree Analysis](./source-tree-analysis.md) - Directory structure and file organization
- [Development Guide](./development-guide.md) - Setup, commands, and common tasks

### Existing Documentation
- [README.md](../README.md) - Project overview and getting started (root)
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Async pipeline and HAL design (root)
- [SCENARIOS.md](../SCENARIOS.md) - Interaction patterns (root)
- [AGENTS.md](../AGENTS.md) - AI coding agent guidance (root)

## Getting Started

### Prerequisites
- Python 3.12+
- C++ Build Tools (for llama-cpp-python)
- uv package manager

### Installation
```bash
uv sync --extra dev
```

### Download Models
```bash
uv run python scripts/download_models.py
```

### Run
```bash
uv run python src/app/main.py
```

### Controls
- **Speaker A (Space)**: English → Russian
- **Speaker B (Alt)**: Russian → English
- **Hold** to speak, **Release** to hear translation
- Press anytime to interrupt (barge-in)

## Configuration

The application uses `config.yaml` with multiple profiles:

- **desktop_rtx4070**: Windows development with GPU
- **rpi_deployment**: Raspberry Pi production

See [Development Guide](./development-guide.md#configuration-profiles) for detailed configuration options.

## Testing

```bash
uv run pytest
```

The project includes 12 tests covering:
- Unit tests for individual components
- Integration tests for the async pipeline

## Development

See the [Development Guide](./development-guide.md) for:
- Complete setup instructions
- Development commands
- Code style guidelines
- Common development tasks

## Platforms

| Platform | Input | LLM | Status |
|----------|-------|-----|--------|
| Windows | Keyboard (pynput) | GPU/CPU | Supported |
| Raspberry Pi | GPIO (to be implemented) | CPU | Planned |
