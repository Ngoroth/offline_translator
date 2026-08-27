from typing import cast
from unittest.mock import MagicMock, patch

from pathlib import Path

from app.core.config import AppSettings, AudioSettings, LLMSettings, STTSettings, TTSSettings
from app.core.performance import (
    PerformanceEventEmitter,
    ResourceSnapshot,
    _read_proc_value,
    audio_duration_ms,
    build_profile_fingerprint,
)


def test_audio_duration_ms_handles_samples_and_invalid_runtime_values() -> None:
    assert audio_duration_ms(16000, 16000) == 1000
    assert audio_duration_ms(0, 16000) == 0
    assert audio_duration_ms(16000, cast(int, MagicMock())) == 0


def test_read_proc_value_accepts_meminfo_and_vmstat_formats(tmp_path: Path) -> None:
    proc_file = tmp_path / "proc"
    proc_file.write_text("MemAvailable: 123 kB\npswpin 7\n", encoding="utf-8")

    assert _read_proc_value(proc_file, "MemAvailable") == 123
    assert _read_proc_value(proc_file, "pswpin") == 7


def test_emitter_payload_contains_metadata_but_no_user_content() -> None:
    emitter = PerformanceEventEmitter(run_id="run-1")

    with patch("app.core.performance.logger") as mock_logger:
        emitter.emit("session-1", "llm_end", input_chars=12, output_chars=8)

    payload = mock_logger.bind.call_args.kwargs["performance_event"]
    assert payload["run_id"] == "run-1"
    assert payload["trial_id"] == "session-1"
    assert payload["phase"] == "llm_end"
    assert payload["input_chars"] == 12
    assert payload["output_chars"] == 8
    assert "text" not in payload
    assert "secret user phrase" not in str(payload)


def test_resource_snapshot_is_nested_in_event() -> None:
    emitter = PerformanceEventEmitter(run_id="run-1")
    snapshot = ResourceSnapshot(
        mem_available_kb=100,
        process_vmrss_kb=200,
        swap_free_kb=300,
        pswpin=4,
        pswpout=5,
        cpu_freq_khz=1800000,
        cpu_governor="performance",
        temperature_c=55.5,
        vcgencmd_throttled="throttled=0x0",
    )

    with (
        patch("app.core.performance.collect_resource_snapshot", return_value=snapshot),
        patch("app.core.performance.logger") as mock_logger,
    ):
        emitter.begin_trial("session-1")

    resource_call = mock_logger.bind.call_args_list[1]
    payload = resource_call.kwargs["performance_event"]
    assert payload["phase"] == "resource_start"
    assert payload["resource"] == snapshot.to_payload()


def test_run_fingerprint_is_attached_and_trial_kind_is_explicit() -> None:
    emitter = PerformanceEventEmitter(run_id="run-1", trial_kind="cold")

    with patch("app.core.performance.logger") as mock_logger:
        emitter.begin_run("session-1", {"profile": "rpi_deployment", "n_threads": 4})
        emitter.begin_trial("session-1")

    run_payload = mock_logger.bind.call_args_list[0].kwargs["performance_event"]
    trial_payload = mock_logger.bind.call_args_list[1].kwargs["performance_event"]
    assert run_payload["phase"] == "run_start"
    assert run_payload["trial_kind"] == "cold"
    assert trial_payload["profile_fingerprint"] == {
        "profile": "rpi_deployment",
        "n_threads": 4,
    }


def test_profile_fingerprint_includes_llm_seed(tmp_path: Path) -> None:
    llm_settings = LLMSettings(model_path=str(tmp_path / "model.gguf"), seed=1)
    settings = AppSettings(
        audio=AudioSettings(),
        stt=STTSettings(model_path="tiny"),
        llm=llm_settings,
        tts=TTSSettings(model_path="voice.onnx"),
    )

    fingerprint = build_profile_fingerprint(settings, "test", None)
    llm_fingerprint = cast(dict[str, object], fingerprint["llm"])

    assert llm_fingerprint["seed"] == 1
