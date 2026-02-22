import urllib.request
from pathlib import Path


def download_file(url: str, dest: Path):
    if dest.exists():
        print(f"Already exists: {dest}")
        return
    print(f"Downloading {url} to {dest}...")
    dest.parent.mkdir(parents=True, exist_ok=True)
    _ = urllib.request.urlretrieve(url, dest)


def main():
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"

    # STT Models (handled by faster-whisper usually, but let's point out where they go)
    # Whisper models are downloaded automatically by the library to ~/.cache/huggingface
    # But we want them in models/stt for offline use.

    # LLM Model (Qwen 3 Instruct)
    # Desktop: Qwen 3 4B Instruct
    llm_desktop_url = "https://huggingface.co/bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    download_file(llm_desktop_url, models_dir / "llm" / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf")

    # Raspberry Pi: Qwen 3 0.6B Instruct
    llm_pi_url = "https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q8_0.gguf"
    download_file(llm_pi_url, models_dir / "llm" / "Qwen3-0.6B-Q8_0.gguf")

    # TTS Model (Piper)
    # English
    tts_en_model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx"
    tts_en_config_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts_r/medium/en_US-libritts_r-medium.onnx.json"
    download_file(tts_en_model_url, models_dir / "tts" / "en_US-libritts_r-medium.onnx")
    download_file(tts_en_config_url, models_dir / "tts" / "en_US-libritts_r-medium.onnx.json")

    # Russian
    tts_ru_model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx"
    tts_ru_config_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx.json"
    download_file(tts_ru_model_url, models_dir / "tts" / "ru_RU-denis-medium.onnx")
    download_file(tts_ru_config_url, models_dir / "tts" / "ru_RU-denis-medium.onnx.json")

    print(
        "\nModels downloaded successfully (STT models will be downloaded on first run by faster-whisper)."
    )


if __name__ == "__main__":
    main()
