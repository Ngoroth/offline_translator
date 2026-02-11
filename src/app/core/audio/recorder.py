import asyncio
import subprocess
import numpy as np
import threading
from loguru import logger
from numpy.typing import NDArray


class AudioRecorder:
    """
    AudioRecorder implementation using native 'arecord' (ALSA) via subprocess.
    This avoids PortAudio sample rate issues on Raspberry Pi by offloading resampling to ALSA tools.
    """

    sample_rate: int
    device_index: int | str | None
    process: subprocess.Popen[bytes] | None
    buffer: list[NDArray[np.float32]]
    _queue: asyncio.Queue[NDArray[np.float32]]
    recording: bool
    _loop: asyncio.AbstractEventLoop
    _read_thread: threading.Thread | None

    def __init__(self, sample_rate: int = 16000, device_index: int | str | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.process = None
        self.buffer = []
        self._queue = asyncio.Queue()
        self.recording = False
        self._read_thread = None
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("AudioRecorder initialized outside of running loop.")

    def start(self) -> None:
        if self.recording:
            return

        self.buffer = []
        # Clear queue
        while not self._queue.empty():
            try:
                _ = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.recording = True

        # Determine device string
        # If device_index is "hw:2,0" or "plughw:2,0", use it.
        # If it's an int (from portaudio index), we might need to convert,
        # but for now we assume config provides the ALSA string directly.
        device = str(self.device_index) if self.device_index else "default"

        # Construct arecord command
        # -D <device> : Select PCM by name
        # -f S16_LE   : Signed 16 bit Little Endian (Standard)
        # -r <rate>   : Target sample rate (arecord/ALSA handles conversion if plughw is used)
        # -c 1        : Mono
        # -t raw      : Raw PCM output (no WAV header)
        cmd = [
            "arecord",
            "-D",
            device,
            "-f",
            "S16_LE",
            "-r",
            str(self.sample_rate),
            "-c",
            "1",
            "-t",
            "raw",
            # "-" means stdout, but it's implicit when not specifying file?
            # arecord usually writes to stdout if filename is '-'
            "-",
        ]

        logger.info(f"Starting native recorder: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=16384,  # Reasonable buffer size
            )

            # Start reading thread
            self._read_thread = threading.Thread(target=self._read_stdout)
            self._read_thread.start()

        except Exception as e:
            logger.error(f"Failed to start arecord: {e}")
            self.recording = False

    def stop(self) -> NDArray[np.float32]:
        self.recording = False

        if self.process:
            self.process.terminate()
            try:
                _ = self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()

            if self.process.stderr:
                err = self.process.stderr.read()
                if err:
                    logger.debug(f"arecord stderr: {err.decode(errors='ignore')}")

            self.process = None

        if self._read_thread:
            self._read_thread.join()
            self._read_thread = None

        data = self.extract_buffer()

        # DEBUG: Save to file for verification
        try:
            import soundfile as sf

            sf.write("debug_native_rec.wav", data, self.sample_rate)
            logger.info(f"Saved debug_native_rec.wav ({len(data)} samples)")
        except Exception:
            pass

        return data

    def _read_stdout(self) -> None:
        """Background thread to read from arecord stdout."""
        if not self.process or not self.process.stdout:
            return

        chunk_size = 4096 * 2  # 4096 samples * 2 bytes (16-bit)

        while self.recording and self.process.poll() is None:
            try:
                raw_bytes = self.process.stdout.read(chunk_size)
                if not raw_bytes:
                    break

                # Convert raw S16_LE bytes to float32
                # 1. From buffer to int16 array
                int16_data = np.frombuffer(raw_bytes, dtype=np.int16)

                # 2. Convert to float32 and normalize to [-1.0, 1.0]
                float_data = int16_data.astype(np.float32) / 32768.0

                if self.recording:
                    self.buffer.append(float_data)
                    _ = self._loop.call_soon_threadsafe(self._queue.put_nowait, float_data)

            except Exception as e:
                logger.error(f"Error reading from arecord: {e}")
                break

    async def get_chunk(self) -> NDArray[np.float32]:
        return await self._queue.get()

    def get_last_chunk(self, num_samples: int) -> NDArray[np.float32]:
        if not self.buffer:
            return np.array([], dtype=np.float32)
        full = np.concatenate(self.buffer)
        if len(full) < num_samples:
            return full.flatten()
        return full[-num_samples:].flatten()

    def extract_buffer(self) -> NDArray[np.float32]:
        if not self.buffer:
            return np.array([], dtype=np.float32)
        data = np.concatenate(self.buffer)
        self.buffer = []
        return data.flatten()
