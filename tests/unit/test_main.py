from types import SimpleNamespace
from typing import final
from unittest.mock import MagicMock
from pathlib import Path

import pytest

from app import main as app_main
from app.core.audio.recorder import AudioRecorder
from app.core.audio.recorder_sounddevice import SoundDeviceAudioRecorder
from app.core.audio.recorder_selector import select_recorder_factory


def _noop() -> None:
    return None


def _raise_stop_error() -> list[object]:
    raise RuntimeError("stop")


class _StubSTT:
    async def warmup(self) -> None:
        return None


def test_parse_cli_args_supports_profile_flag() -> None:
    args = app_main.parse_cli_args(["--profile", "rpi_deployment"])

    assert args.profile == "rpi_deployment"


def test_parse_cli_args_disables_abbreviated_flags() -> None:
    with pytest.raises(SystemExit):
        app_main.parse_cli_args(["--prof", "rpi_deployment"])


def test_parse_cli_args_supports_playback_override_boolean_flags() -> None:
    enabled_args = app_main.parse_cli_args(["--playback-during-recording"])
    disabled_args = app_main.parse_cli_args(["--no-playback-during-recording"])
    default_args = app_main.parse_cli_args([])

    assert enabled_args.playback_during_recording is True
    assert disabled_args.playback_during_recording is False
    assert default_args.playback_during_recording is None


def test_cli_forwards_none_profile_when_flag_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | bool | None] = {}

    async def fake_main(
        profile_override: str | None = None,
        playback_during_recording_override: bool | None = None,
    ) -> int:
        captured["profile_override"] = profile_override
        captured["playback_during_recording_override"] = playback_during_recording_override
        return 0

    monkeypatch.setattr(app_main, "main", fake_main)

    result = app_main.cli([])

    assert result == 0
    assert captured["profile_override"] is None
    assert captured["playback_during_recording_override"] is None


def test_cli_forwards_playback_override_when_flag_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str | bool | None] = {}

    async def fake_main(
        profile_override: str | None = None,
        playback_during_recording_override: bool | None = None,
    ) -> int:
        captured["profile_override"] = profile_override
        captured["playback_during_recording_override"] = playback_during_recording_override
        return 0

    monkeypatch.setattr(app_main, "main", fake_main)

    result = app_main.cli(["--playback-during-recording"])

    assert result == 0
    assert captured["profile_override"] is None
    assert captured["playback_during_recording_override"] is True


@pytest.mark.asyncio
async def test_main_logs_active_profile_and_loads_override(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = MagicMock()
    settings.platform = "linux"
    settings.input_mode = "evdev"
    settings.model_dump.return_value = {}

    load_settings_mock = MagicMock(return_value=settings)
    logger_mock = MagicMock()

    class StubVerifier:
        def __init__(self, _settings: object) -> None:
            pass

        def verify_all(self) -> bool:
            return True

    monkeypatch.setattr(app_main, "setup_logging", _noop)
    monkeypatch.setattr(app_main, "load_settings", load_settings_mock)
    monkeypatch.setattr(app_main, "StartupVerifier", StubVerifier)
    monkeypatch.setattr(app_main, "list_audio_devices", _raise_stop_error)
    monkeypatch.setattr(app_main, "logger", logger_mock)

    result = await app_main.main(profile_override="rpi_deployment")

    assert result == 1
    load_settings_mock.assert_called_once_with(profile_override="rpi_deployment")
    assert any(
        call.args and call.args[0] == "Profile: rpi_deployment"
        for call in logger_mock.info.call_args_list
    )


@pytest.mark.asyncio
async def test_main_returns_non_zero_for_invalid_profile_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger_mock = MagicMock()

    monkeypatch.setattr(app_main, "setup_logging", _noop)
    monkeypatch.setattr(
        app_main, "load_settings", MagicMock(side_effect=ValueError("missing_profile"))
    )
    monkeypatch.setattr(app_main, "logger", logger_mock)

    result = await app_main.main(profile_override="missing_profile")

    assert result == 1
    assert any(
        call.args and "missing_profile" in call.args[0]
        for call in logger_mock.exception.call_args_list
    )


def test_select_recorder_factory_explicit_platform_mappings() -> None:
    assert select_recorder_factory("windows") is SoundDeviceAudioRecorder
    assert select_recorder_factory("linux") is AudioRecorder
    assert select_recorder_factory("rpi") is AudioRecorder


def test_select_recorder_factory_auto_uses_host_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def windows_host() -> str:
        return "Windows"

    monkeypatch.setattr("app.core.audio.recorder_selector.platform.system", windows_host)
    assert select_recorder_factory("auto") is SoundDeviceAudioRecorder

    def linux_host() -> str:
        return "Linux"

    monkeypatch.setattr("app.core.audio.recorder_selector.platform.system", linux_host)
    assert select_recorder_factory("auto") is AudioRecorder


@pytest.mark.asyncio
async def test_main_uses_profile_platform_to_create_recorder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder_calls: list[dict[str, object]] = []
    selector_platforms: list[str] = []

    def fake_recorder_factory(*, sample_rate: int, device_index: int | str | None) -> object:
        recorder_calls.append({"sample_rate": sample_rate, "device_index": device_index})
        return object()

    def fake_select_recorder_factory(platform_name: str) -> object:
        selector_platforms.append(platform_name)
        return fake_recorder_factory

    @final
    class StubSettings:
        platform = "windows"
        input_mode = "keyboard"
        audio = SimpleNamespace(
            sample_rate=16000,
            input_device=None,
            input_device_index=None,
            output_device=None,
            output_device_index=None,
        )
        tts = SimpleNamespace(model_path="tts.onnx")
        speakers: dict[str, object] = {
            "a": SimpleNamespace(key="space", tts_model="tts_ru.onnx"),
            "b": SimpleNamespace(key="alt", tts_model="tts_en.onnx"),
        }
        stt = SimpleNamespace()
        llm = SimpleNamespace()

        def model_dump(self, mode: str = "json") -> dict[str, object]:
            del mode
            return {}

    settings = StubSettings()

    class StubInputHandler:
        def start(self) -> None:
            return None

    input_handler = StubInputHandler()

    class StubVerifier:
        def __init__(self, _settings: object) -> None:
            pass

        def verify_all(self) -> bool:
            return True

    @final
    class StubOrchestrator:
        pipeline: object
        input_provider: object

        def __init__(self, pipeline: object, input_provider: object) -> None:
            self.pipeline = pipeline
            self.input_provider = input_provider

        async def run(self) -> None:
            return None

    def load_settings_stub(profile_override: str | None = None) -> StubSettings:
        del profile_override
        return settings

    def current_profile_stub() -> str:
        return "desktop_rtx4070"

    def list_devices_stub() -> list[object]:
        return []

    def resolve_input_stub(_value: str | int | None) -> int:
        del _value
        return 3

    def resolve_output_stub(_value: str | int | None) -> int:
        del _value
        return 5

    def input_handler_stub(_settings: object) -> StubInputHandler:
        del _settings
        return input_handler

    def player_stub(*, sample_rate: int, device_index: int | str | None) -> object:
        del sample_rate
        del device_index
        return object()

    def stt_stub(_stt_settings: object) -> object:
        del _stt_settings
        return _StubSTT()

    def llm_stub(_llm_settings: object) -> object:
        del _llm_settings
        return object()

    def tts_stub(_tts_settings: object, extra_models: list[str]) -> object:
        del _tts_settings
        del extra_models
        return object()

    def pipeline_stub(
        *,
        settings: object,
        stt: object,
        llm: object,
        tts: object,
        recorder: object,
        player: object,
    ) -> object:
        del settings
        del stt
        del llm
        del tts
        del recorder
        del player
        return object()

    monkeypatch.setattr(app_main, "setup_logging", _noop)
    monkeypatch.setattr(app_main, "load_settings", load_settings_stub)
    monkeypatch.setattr(app_main, "_get_current_profile_key", current_profile_stub)
    monkeypatch.setattr(app_main, "StartupVerifier", StubVerifier)
    monkeypatch.setattr(app_main, "list_audio_devices", list_devices_stub)
    monkeypatch.setattr(app_main, "resolve_input_device", resolve_input_stub)
    monkeypatch.setattr(app_main, "resolve_output_device", resolve_output_stub)
    monkeypatch.setattr(app_main, "get_input_handler", input_handler_stub)
    monkeypatch.setattr(app_main, "select_recorder_factory", fake_select_recorder_factory)
    monkeypatch.setattr(app_main, "AudioPlayer", player_stub)
    monkeypatch.setattr(app_main, "STTService", stt_stub)
    monkeypatch.setattr(app_main, "LLMService", llm_stub)
    monkeypatch.setattr(app_main, "TTSService", tts_stub)
    monkeypatch.setattr(app_main, "TranslationPipeline", pipeline_stub)
    monkeypatch.setattr(app_main, "Orchestrator", StubOrchestrator)

    result = await app_main.main(profile_override="desktop_rtx4070")

    assert result == 0
    assert selector_platforms == ["windows"]
    assert recorder_calls == [{"sample_rate": 16000, "device_index": 3}]


@pytest.mark.asyncio
async def test_main_applies_runtime_playback_override_only_in_memory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    recorder_calls: list[dict[str, object]] = []
    config_path = tmp_path / "config.yaml"
    original_config = "current_profile: desktop_rtx4070\n"
    config_path.write_text(original_config, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    @final
    class StubSettings:
        platform = "windows"
        input_mode = "keyboard"
        audio = SimpleNamespace(
            sample_rate=16000,
            input_device=None,
            input_device_index=None,
            output_device=None,
            output_device_index=None,
            playback_during_recording=False,
        )
        tts = SimpleNamespace(model_path="tts.onnx")
        speakers: dict[str, object] = {
            "a": SimpleNamespace(key="space", tts_model="tts_ru.onnx"),
            "b": SimpleNamespace(key="alt", tts_model="tts_en.onnx"),
        }
        stt = SimpleNamespace()
        llm = SimpleNamespace()

        def model_dump(self, mode: str = "json") -> dict[str, object]:
            del mode
            return {}

    settings = StubSettings()

    class StubInputHandler:
        def start(self) -> None:
            return None

    input_handler = StubInputHandler()

    class StubVerifier:
        def __init__(self, _settings: object) -> None:
            pass

        def verify_all(self) -> bool:
            return True

    @final
    class StubOrchestrator:
        pipeline: object
        input_provider: object

        def __init__(self, pipeline: object, input_provider: object) -> None:
            self.pipeline = pipeline
            self.input_provider = input_provider

        async def run(self) -> None:
            return None

    def fake_recorder_factory(*, sample_rate: int, device_index: int | str | None) -> object:
        recorder_calls.append({"sample_rate": sample_rate, "device_index": device_index})
        return object()

    def fake_select_recorder_factory(_platform_name: str) -> object:
        return fake_recorder_factory

    def load_settings_stub(profile_override: str | None = None) -> StubSettings:
        del profile_override
        return settings

    def list_devices_stub() -> list[object]:
        return []

    def resolve_input_stub(_value: str | int | None) -> int:
        del _value
        return 3

    def resolve_output_stub(_value: str | int | None) -> int:
        del _value
        return 5

    def input_handler_stub(_settings: object) -> StubInputHandler:
        del _settings
        return input_handler

    def player_stub(*, sample_rate: int, device_index: int | str | None) -> object:
        del sample_rate
        del device_index
        return object()

    def stt_stub(_stt_settings: object) -> object:
        del _stt_settings
        return _StubSTT()

    def llm_stub(_llm_settings: object) -> object:
        del _llm_settings
        return object()

    def tts_stub(_tts_settings: object, extra_models: list[str]) -> object:
        del _tts_settings
        del extra_models
        return object()

    def pipeline_stub(
        *,
        settings: object,
        stt: object,
        llm: object,
        tts: object,
        recorder: object,
        player: object,
    ) -> object:
        del settings
        del stt
        del llm
        del tts
        del recorder
        del player
        return object()

    monkeypatch.setattr(app_main, "setup_logging", _noop)
    monkeypatch.setattr(app_main, "load_settings", load_settings_stub)
    monkeypatch.setattr(app_main, "StartupVerifier", StubVerifier)
    monkeypatch.setattr(app_main, "list_audio_devices", list_devices_stub)
    monkeypatch.setattr(app_main, "resolve_input_device", resolve_input_stub)
    monkeypatch.setattr(app_main, "resolve_output_device", resolve_output_stub)
    monkeypatch.setattr(app_main, "get_input_handler", input_handler_stub)
    monkeypatch.setattr(app_main, "select_recorder_factory", fake_select_recorder_factory)
    monkeypatch.setattr(app_main, "AudioPlayer", player_stub)
    monkeypatch.setattr(app_main, "STTService", stt_stub)
    monkeypatch.setattr(app_main, "LLMService", llm_stub)
    monkeypatch.setattr(app_main, "TTSService", tts_stub)
    monkeypatch.setattr(app_main, "TranslationPipeline", pipeline_stub)
    monkeypatch.setattr(app_main, "Orchestrator", StubOrchestrator)

    result = await app_main.main(playback_during_recording_override=True)

    assert result == 0
    assert settings.audio.playback_during_recording is True
    assert recorder_calls == [{"sample_rate": 16000, "device_index": 3}]
    assert config_path.read_text(encoding="utf-8") == original_config
