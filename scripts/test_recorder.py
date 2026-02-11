import asyncio
import sys
import os
import soundfile as sf

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from app.core.audio.recorder import AudioRecorder
from loguru import logger


async def test_recording():
    logger.info("Testing AudioRecorder with resampling...")

    # Use config values we discovered
    # device_index="hw:2,0" is safer passed as string if supported, or index if portaudio enumerates it
    # We will try passing None first (default), or we might need to find index for PortAudio

    recorder = AudioRecorder(sample_rate=16000, device_index=None)

    logger.info("Starting recording for 5 seconds... SPEAK NOW!")
    recorder.start()

    await asyncio.sleep(5)

    logger.info("Stopping...")
    audio_data = recorder.stop()

    logger.info(f"Recorded {len(audio_data)} samples.")

    filename = "test_resampled.wav"
    sf.write(filename, audio_data, 16000)
    logger.info(f"Saved to {filename}")

    # Verify content (simple RMS check)
    from typing import cast

    audio_list: list[float] = cast(list[float], audio_data.tolist())
    squared_sum = sum(x * x for x in audio_list)
    mean_val: float = squared_sum / len(audio_list) if audio_list else 0.0
    import math

    rms: float = math.sqrt(mean_val)
    logger.info(f"RMS Amplitude: {rms:.4f}")

    if rms < 0.001:
        logger.warning("WARNING: Audio is suspiciously quiet! Check microphone input.")
    else:
        logger.info("Audio levels look OK.")


if __name__ == "__main__":
    asyncio.run(test_recording())
