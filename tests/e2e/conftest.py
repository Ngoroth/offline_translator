"""E2E test fixtures for model downloads and caching.

Provides session-scoped fixtures that prefer already-downloaded models
in the repo's models/ directory and fall back to downloading from
Hugging Face Hub.
"""

from pathlib import Path

import pytest
from huggingface_hub import hf_hub_download, snapshot_download

# Cache directory for test models (~535MB total)
CACHE_DIR = Path.home() / ".cache" / "offline_translator_tests"

# Repo-local models directory (preferred source)
MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

# STT model config
STT_REPO = "Systran/faster-whisper-tiny"

# LLM model config
LLM_REPO = "unsloth/Qwen3.5-0.8B-GGUF"
LLM_FILE = "Qwen3.5-0.8B-Q4_K_M.gguf"

# TTS model config
TTS_REPO = "rhasspy/piper-voices"
TTS_FOLDER = "en/en_US/lessac/medium"
TTS_ONNX_FILE = "en_US-lessac-medium.onnx"
TTS_JSON_FILE = "en_US-lessac-medium.onnx.json"


@pytest.fixture(scope="session")
def stt_model_path() -> Path:
    """Return the STT model path.

    Prefers a local faster-whisper model directory in models/stt, otherwise
    downloads and caches Whisper-tiny for E2E tests.

    faster-whisper expects a directory containing model files,
    not a single file. Uses snapshot_download to get full model.

    Returns:
        Path to the model directory.
    """
    local = MODELS_DIR / "stt" / "tiny"
    if (local / "model.bin").exists():
        return local
    return Path(
        snapshot_download(
            repo_id=STT_REPO,
            cache_dir=CACHE_DIR,
        )
    )


@pytest.fixture(scope="session")
def llm_model_path() -> Path:
    """Return the path to the Qwen3.5-0.8B GGUF model.

    Prefers the repo-local copy in models/llm (used by the rpi profile),
    otherwise downloads and caches Qwen3.5-0.8B-Q4_K_M.gguf.

    Returns:
        Path to the GGUF model file.
    """
    local = MODELS_DIR / "llm" / LLM_FILE
    if local.exists():
        return local
    return Path(
        hf_hub_download(
            repo_id=LLM_REPO,
            filename=LLM_FILE,
            cache_dir=CACHE_DIR,
        )
    )


@pytest.fixture(scope="session")
def tts_model_path() -> Path:
    """Return the path to a Piper TTS model.

    Prefers the repo-local English voice in models/tts, otherwise downloads
    and caches the Piper TTS model for E2E tests.

    Returns:
        Path to the ONNX model file.
    """
    local = MODELS_DIR / "tts" / "en_US-libritts_r-medium.onnx"
    if local.exists() and local.with_suffix(".onnx.json").exists():
        return local

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
