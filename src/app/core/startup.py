"""Startup verification for the offline translator application.

Validates that all required models exist and audio devices are available
before user interaction begins. Exits with actionable error messages
if prerequisites are missing.
"""

import sys
from pathlib import Path

from app.core.audio.devices import (
    list_audio_devices,
    resolve_input_device,
    resolve_output_device,
)
from app.core.audio.recorder import AudioDeviceError
from app.core.config import AppSettings


class StartupVerifier:
    """Verifies all startup prerequisites before the application runs.

    Checks:
    1. Model files exist (STT, LLM, TTS, speaker voices)
    2. Audio devices are available

    Exits with non-zero code if any check fails:
    - Exit code 1: Missing model files
    - Exit code 2: No audio devices available
    """

    settings: AppSettings
    exit_code: int

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.exit_code = 0

    def verify_all(self) -> bool:
        """Run all verification checks.

        Returns:
            True if all checks pass.

        Note:
            Calls sys.exit() with appropriate exit code if any check fails.
        """
        if not self.verify_models():
            sys.exit(self.exit_code)
        if not self.verify_audio_devices():
            sys.exit(self.exit_code)
        return True

    def verify_models(self) -> bool:
        """Check that all required model files exist.

        Returns:
            True if all models exist, False otherwise.
            Sets exit_code to 1 on failure.
        """
        missing: list[str] = []

        # STT model - only check if it looks like a local path
        # faster-whisper accepts huggingface IDs that don't need local files
        stt_path = self.settings.stt.model_path
        if stt_path:
            p = Path(stt_path)
            if p.is_absolute() or stt_path.startswith("models/"):
                if not p.exists():
                    missing.append(str(p))

        # LLM model - always required
        llm_path = self.settings.llm.model_path
        if llm_path:
            p = Path(llm_path)
            if not p.exists():
                missing.append(str(p))

        # Default TTS model
        tts_path = self.settings.tts.model_path
        if tts_path:
            p = Path(tts_path)
            if not p.exists():
                missing.append(str(p))

        # Per-speaker voices (target language voices)
        for speaker in self.settings.speakers.values():
            tts_path = speaker.tts_model
            if tts_path:
                p = Path(tts_path)
                if not p.exists():
                    missing.append(str(p))

        if missing:
            print("ERROR: Missing model files:")
            for path in missing:
                print(f"  - {path}")
            print()
            print("Run: uv run python scripts/download_models.py")
            self.exit_code = 1
            return False

        return True

    def verify_audio_devices(self) -> bool:
        """Check that audio devices are available.

        Returns:
            True if both input and output devices are available, False otherwise.
            Sets exit_code to 2 on failure.
        """
        try:
            _ = resolve_input_device(None)
            _ = resolve_output_device(None)
        except AudioDeviceError:
            print("ERROR: No audio devices available")
            print()
            print("Available devices:")

            devices = list_audio_devices()
            for dev in devices:
                kinds: list[str] = []
                if dev.is_input:
                    kinds.append("input")
                if dev.is_output:
                    kinds.append("output")
                kind_str = ", ".join(kinds) if kinds else "unknown"
                print(f"  [{dev.index}] {dev.name} ({kind_str})")

            self.exit_code = 2
            return False

        return True
