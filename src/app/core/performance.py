"""Low-overhead, privacy-preserving performance instrumentation."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid
from copy import deepcopy
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from loguru import logger

if TYPE_CHECKING:
    from app.core.config import AppSettings


PERFORMANCE_EVENT_KEY = "performance_event"
TrialKind = Literal["cold", "warm"]


def _package_version(distribution: str) -> str | None:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def _revision() -> str:
    configured = os.getenv("PERF_REVISION")
    if configured:
        return configured
    try:
        result = subprocess.run(
            ("git", "rev-parse", "--short", "HEAD"),
            capture_output=True,
            text=True,
            check=False,
            timeout=1,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def build_profile_fingerprint(
    settings: "AppSettings",
    profile_name: str,
    voice: str | None,
) -> dict[str, object]:
    """Build stable, non-content metadata identifying one benchmark run."""
    return {
        "profile": profile_name,
        "revision": _revision(),
        "voice": voice,
        "audio": {
            "sample_rate": settings.audio.sample_rate,
            "channels": settings.audio.channels,
        },
        "stt": {
            "model_path": settings.stt.model_path,
            "beam_size": settings.stt.beam_size,
            "vad_filter": True,
            "auto_harvest": settings.vad.auto_harvest,
        },
        "llm": {
            "model_path": settings.llm.model_path,
            "n_threads": settings.llm.n_threads,
            "n_ctx": settings.llm.context_window,
            "seed": settings.llm.seed,
        },
        "tts": {"default_model_path": settings.tts.model_path},
        "packages": {
            "faster-whisper": _package_version("faster-whisper"),
            "llama-cpp-python": _package_version("llama-cpp-python"),
            "piper-tts": _package_version("piper-tts"),
        },
    }


@dataclass(frozen=True)
class ResourceSnapshot:
    """Best-effort Linux resource readings used to invalidate bad trials."""

    mem_available_kb: int | None
    process_vmrss_kb: int | None
    swap_free_kb: int | None
    pswpin: int | None
    pswpout: int | None
    cpu_freq_khz: int | None
    cpu_governor: str | None
    temperature_c: float | None
    vcgencmd_throttled: str | None

    def to_payload(self) -> dict[str, int | float | str | None]:
        return {
            "mem_available_kb": self.mem_available_kb,
            "process_vmrss_kb": self.process_vmrss_kb,
            "swap_free_kb": self.swap_free_kb,
            "pswpin": self.pswpin,
            "pswpout": self.pswpout,
            "cpu_freq_khz": self.cpu_freq_khz,
            "cpu_governor": self.cpu_governor,
            "temperature_c": self.temperature_c,
            "vcgencmd_throttled": self.vcgencmd_throttled,
        }


def _read_proc_value(path: Path, key: str) -> int | None:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                name, _, value = line.partition(":")
            else:
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    continue
                name, value = parts
            if name != key:
                continue
            value_part = value.strip().split(maxsplit=1)[0]
            return int(value_part)
    except (OSError, ValueError, IndexError):
        return None
    return None


def _read_text(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _read_temperature() -> float | None:
    raw = _read_text(Path("/sys/class/thermal/thermal_zone0/temp"))
    if raw is None:
        return None
    try:
        return int(raw) / 1000.0
    except ValueError:
        return None


def _read_vcgencmd() -> str | None:
    command = shutil.which("vcgencmd")
    if command is None:
        return None
    try:
        result = subprocess.run(
            (command, "get_throttled"),
            capture_output=True,
            text=True,
            check=False,
            timeout=1,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value or None


def collect_resource_snapshot() -> ResourceSnapshot:
    """Collect optional Linux/Raspberry Pi readings without adding dependencies."""

    meminfo = Path("/proc/meminfo")
    vmstat = Path("/proc/vmstat")
    status = Path("/proc/self/status")
    mem_available = _read_proc_value(meminfo, "MemAvailable")
    swap_free = _read_proc_value(meminfo, "SwapFree")
    process_vmrss = _read_proc_value(status, "VmRSS")
    pswpin = _read_proc_value(vmstat, "pswpin")
    pswpout = _read_proc_value(vmstat, "pswpout")

    frequency_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    governor_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    frequency_raw = _read_text(frequency_path)
    try:
        cpu_freq_khz = int(frequency_raw) if frequency_raw is not None else None
    except ValueError:
        cpu_freq_khz = None

    return ResourceSnapshot(
        mem_available_kb=mem_available,
        process_vmrss_kb=process_vmrss,
        swap_free_kb=swap_free,
        pswpin=pswpin,
        pswpout=pswpout,
        cpu_freq_khz=cpu_freq_khz,
        cpu_governor=_read_text(governor_path),
        temperature_c=_read_temperature(),
        vcgencmd_throttled=_read_vcgencmd(),
    )


class PerformanceEventEmitter:
    """Emit structured timing events while keeping user content out of logs."""

    run_id: str

    def __init__(
        self,
        run_id: str | None = None,
        trial_kind: TrialKind | None = None,
    ) -> None:
        self.run_id = run_id or os.getenv("PERF_RUN_ID") or str(uuid.uuid4())
        configured_kind: str | None = trial_kind or os.getenv("PERF_TRIAL_KIND")
        self.trial_kind: TrialKind | None = (
            cast(TrialKind, configured_kind)
            if configured_kind in {"cold", "warm"}
            else None
        )
        self.profile_fingerprint: dict[str, object] | None = None
        self._run_started: bool = False
        self._trial_ids: dict[str, str] = {}
        self._finished_sessions: set[str] = set()

    def _trial_id_for(self, session_id: str) -> str:
        return self._trial_ids.get(session_id, session_id)

    def _emit_payload(self, payload: dict[str, object]) -> None:
        if self.profile_fingerprint is not None:
            payload["profile_fingerprint"] = deepcopy(self.profile_fingerprint)
        logger.bind(performance_event=payload).info("performance_event")

    def begin_run(self, session_id: str, fingerprint: Mapping[str, object]) -> None:
        """Emit exactly one immutable run fingerprint before trial events."""
        if self._run_started:
            return
        self.profile_fingerprint = deepcopy(dict(fingerprint))
        self._run_started = True
        self.emit(session_id, "run_start")

    def emit(
        self,
        session_id: str,
        phase: str,
        *,
        audio_ms: int | None = None,
        input_chars: int | None = None,
        output_chars: int | None = None,
    ) -> None:
        payload: dict[str, object] = {
            "run_id": self.run_id,
            "trial_id": self._trial_id_for(session_id),
            "session_id": session_id,
            "phase": phase,
            "monotonic_ns": time.perf_counter_ns(),
            "audio_ms": audio_ms,
            "input_chars": input_chars,
            "output_chars": output_chars,
            "trial_kind": self.trial_kind,
        }
        self._emit_payload(payload)

    def begin_trial(self, session_id: str) -> None:
        """Register a trial and capture its starting resource snapshot."""

        if session_id in self._trial_ids:
            return
        self._trial_ids[session_id] = session_id
        self.emit(session_id, "trial_start")
        self.emit_resource_snapshot(session_id, "resource_start")

    def emit_resource_snapshot(self, session_id: str, phase: str) -> None:
        payload: dict[str, object] = {
            "run_id": self.run_id,
            "trial_id": self._trial_id_for(session_id),
            "session_id": session_id,
            "phase": phase,
            "monotonic_ns": time.perf_counter_ns(),
            "audio_ms": None,
            "input_chars": None,
            "output_chars": None,
            "trial_kind": self.trial_kind,
            "resource": collect_resource_snapshot().to_payload(),
        }
        self._emit_payload(payload)

    def finish_trial(self, session_id: str, phase: str = "trial_end") -> None:
        """Capture end resources once, including cancelled trials."""

        if session_id in self._finished_sessions:
            return
        self.emit_resource_snapshot(session_id, "resource_end")
        self.emit(session_id, phase)
        self._finished_sessions.add(session_id)


def audio_duration_ms(sample_count: object, sample_rate: object) -> int:
    """Convert an audio sample count to an integer duration for event metadata."""

    if (
        not isinstance(sample_count, int)
        or not isinstance(sample_rate, int)
        or sample_count <= 0
        or sample_rate <= 0
    ):
        return 0
    return round(sample_count * 1000 / sample_rate)
