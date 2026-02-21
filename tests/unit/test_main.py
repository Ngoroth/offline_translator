from unittest.mock import MagicMock

import pytest

from app import main as app_main


def test_parse_cli_args_supports_profile_flag() -> None:
    args = app_main.parse_cli_args(["--profile", "rpi_deployment"])

    assert args.profile == "rpi_deployment"


def test_parse_cli_args_disables_abbreviated_flags() -> None:
    with pytest.raises(SystemExit):
        app_main.parse_cli_args(["--prof", "rpi_deployment"])


def test_cli_forwards_none_profile_when_flag_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | None] = {}

    async def fake_main(profile_override: str | None = None) -> int:
        captured["profile_override"] = profile_override
        return 0

    monkeypatch.setattr(app_main, "main", fake_main)

    result = app_main.cli([])

    assert result == 0
    assert captured["profile_override"] is None


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

    monkeypatch.setattr(app_main, "setup_logging", lambda: None)
    monkeypatch.setattr(app_main, "load_settings", load_settings_mock)
    monkeypatch.setattr(app_main, "StartupVerifier", StubVerifier)
    monkeypatch.setattr(
        app_main, "list_audio_devices", lambda: (_ for _ in ()).throw(RuntimeError("stop"))
    )
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

    monkeypatch.setattr(app_main, "setup_logging", lambda: None)
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
