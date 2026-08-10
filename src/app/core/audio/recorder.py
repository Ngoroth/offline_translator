import asyncio
import subprocess

import numpy as np
import threading
from loguru import logger
from numpy.typing import NDArray


class AudioDeviceError(Exception):
    """Exception raised for audio device errors with actionable suggestions."""

    message: str
    device: str | int | None
    suggestion: str

    def __init__(self, message: str, device: str | int | None, suggestion: str) -> None:
        self.message = message
        self.device = device
        self.suggestion = suggestion
        super().__init__(f"{message} (device: {device}). {suggestion}")


class BaseRecorder:
    """Shared state, buffer, and chunk queue for audio recorders."""

    sample_rate: int
    device_index: int | str | None
    buffer: list[NDArray[np.float32]]
    _queue: asyncio.Queue[NDArray[np.float32]]
    recording: bool
    _loop: asyncio.AbstractEventLoop | None

    def __init__(self, sample_rate: int = 16000, device_index: int | str | None = None):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.buffer = []
        self._queue = asyncio.Queue()
        self.recording = False
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
            logger.warning(f"{type(self).__name__} initialized outside of running loop.")

    def _reset(self) -> None:
        """Drop buffered audio and pending queue chunks."""
        self.buffer = []
        while not self._queue.empty():
            try:
                _ = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def get_chunk(self) -> NDArray[np.float32]:
        return await self._queue.get()

    def extract_buffer(self) -> NDArray[np.float32]:
        if not self.buffer:
            return np.array([], dtype=np.float32)
        data = np.concatenate(self.buffer)
        self.buffer = []
        return data.flatten()


class AudioRecorder(BaseRecorder):
    """
    AudioRecorder implementation using native 'arecord' (ALSA) via subprocess.
    This avoids PortAudio sample rate issues on Raspberry Pi by offloading resampling to ALSA tools.
    """

    process: subprocess.Popen[bytes] | None
    _read_thread: threading.Thread | None
    recording: bool

    def __init__(self, sample_rate: int = 16000, device_index: int | str | None = None):
        super().__init__(sample_rate=sample_rate, device_index=device_index)
        self.process = None
        self._read_thread = None

    def start(self) -> None:
        if self.recording:
            return

        self._reset()

        self.recording = True

        device = str(self.device_index) if self.device_index else "default"

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
            "-",
        ]

        logger.info(f"Starting native recorder: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=16384,
            )

            if self.process.poll() is not None:
                stderr = self.process.stderr.read() if self.process.stderr else b""
                raise AudioDeviceError(
                    message="arecord process exited immediately",
                    device=device,
                    suggestion=f"Check if device '{device}' exists. Install alsa-utils if missing. Error: {stderr.decode(errors='ignore')}",
                )

            self._read_thread = threading.Thread(target=self._read_stdout)
            self._read_thread.start()

        except FileNotFoundError:
            self.recording = False
            raise AudioDeviceError(
                message="arecord command not found",
                device=device,
                suggestion="Install alsa-utils: 'sudo apt install alsa-utils' (Linux/RPi) or use Windows audio backend",
            ) from None
        except AudioDeviceError:
            self.recording = False
            raise
        except Exception as e:
            self.recording = False
            logger.error(f"Failed to start arecord: {e}")
            raise AudioDeviceError(
                message=f"Failed to start arecord: {e}",
                device=device,
                suggestion="Check device availability and permissions",
            ) from e

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

        return data

    def _read_stdout(self) -> None:
        if not self.process or not self.process.stdout:
            return

        chunk_size = 4096 * 2

        while self.recording and self.process.poll() is None:
            try:
                raw_bytes = self.process.stdout.read(chunk_size)
                if not raw_bytes:
                    break

                int16_data = np.frombuffer(raw_bytes, dtype=np.int16)
                float_data = int16_data.astype(np.float32) / 32768.0

                if self.recording:
                    self.buffer.append(float_data)
                    if self._loop is not None:
                        _ = self._loop.call_soon_threadsafe(self._queue.put_nowait, float_data)

            except Exception as e:
                logger.error(f"Error reading from arecord: {e}")
                break
