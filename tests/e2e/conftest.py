"""E2E test fixtures for model downloads and caching.

Provides session-scoped fixtures that download and cache test models
from Hugging Face Hub for real model testing.
"""

from pathlib import Path

import pytest
from huggingface_hub import hf_hub_download, snapshot_download

# Cache directory for test models (~535MB total)
CACHE_DIR = Path.home() / ".cache" / "offline_translator_tests"

# STT model config
STT_REPO = "Systran/faster-whisper-tiny"

# LLM model config
LLM_REPO = "Qwen/Qwen3-0.6B-GGUF"
LLM_FILE = "Qwen3-0.6B-Q8_0.gguf"

# TTS model config
TTS_REPO = "rhasspy/piper-voices"
TTS_FOLDER = "en/en_US/lessac/medium"
TTS_ONNX_FILE = "en_US-lessac-medium.onnx"
TTS_JSON_FILE = "en_US-lessac-medium.onnx.json"


@pytest.fixture(scope="session")
def stt_model_path() -> Path:
    """Download and cache Whisper-tiny for E2E tests.

    faster-whisper expects a directory containing model files,
    not a single file. Uses snapshot_download to get full model.

    Returns:
        Path to the model directory.
    """
    return Path(
        snapshot_download(
            repo_id=STT_REPO,
            cache_dir=CACHE_DIR,
        )
    )


@pytest.fixture(scope="session")
def llm_model_path() -> Path:
    """Download and cache Qwen3-0.6B-Q8_0.gguf for E2E tests.

    Uses a small quantized model for fast testing while still
    validating real LLM inference.

    Returns:
        Path to the GGUF model file.
    """
    return Path(
        hf_hub_download(
            repo_id=LLM_REPO,
            filename=LLM_FILE,
            cache_dir=CACHE_DIR,
        )
    )


@pytest.fixture(scope="session")
def tts_model_path() -> Path:
    """Download and cache Piper TTS model for E2E tests.

    Downloads the ONNX model and its JSON config.

    Returns:
        Path to the ONNX model file.
    """
    # Download the ONNX model file
    model_path = Path(
        hf_hub_download(
            repo_id=TTS_REPO,
            filename=f"{TTS_FOLDER}/{TTS_ONNX_FILE}",
            cache_dir=CACHE_DIR,
        )
    )

    # Also download the JSON config (required by Piper)
    _ = hf_hub_download(
        repo_id=TTS_REPO,
        filename=f"{TTS_FOLDER}/{TTS_JSON_FILE}",
        cache_dir=CACHE_DIR,
    )

    return model_path


@pytest.fixture(scope="session")
def tts_model_json_path(tts_model_path: Path) -> Path:
    """Get path to TTS model JSON config.

    Returns:
        Path to the JSON config file (same directory as ONNX).
    """
    return tts_model_path.with_suffix(".onnx.json")


@pytest.fixture
def synthetic_audio_generator():
    """Factory fixture to create synthetic speech-like audio."""
    import numpy as np

    def _create(duration_seconds: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))

        # Mix of fundamental frequency (F0) and formants
        f0 = 150  # Typical male F0
        audio = (
            0.5 * np.sin(2 * np.pi * f0 * t)
            + 0.3 * np.sin(2 * np.pi * 500 * t)
            + 0.2 * np.sin(2 * np.pi * 1500 * t)
        )

        # Add some noise for realism
        noise = np.random.randn(len(t)) * 0.05
        audio = audio + noise

        # Normalize
        audio = audio / np.max(np.abs(audio))

        return audio.astype(np.float32)

    return _create
