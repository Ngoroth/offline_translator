from unittest.mock import patch

import pytest

from app.core.audio.devices import (
    get_default_input_device,
    get_default_output_device,
    list_audio_devices,
    resolve_device,
)


@pytest.fixture
def mock_devices() -> list[dict[str, object]]:
    return [
        {
            "name": "Built-in Microphone",
            "max_input_channels": 2,
            "max_output_channels": 0,
            "default_samplerate": 48000.0,
        },
        {
            "name": "Built-in Speakers",
            "max_input_channels": 0,
            "max_output_channels": 2,
            "default_samplerate": 48000.0,
        },
        {
            "name": "USB Audio Device",
            "max_input_channels": 1,
            "max_output_channels": 2,
            "default_samplerate": 44100.0,
        },
    ]


class TestListAudioDevices:
    def test_list_audio_devices_returns_devices(
        self, mock_devices: list[dict[str, object]]
    ) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.default.device = (0, 1)

            devices = list_audio_devices()

            assert len(devices) == 3
            assert devices[0].name == "Built-in Microphone"
            assert devices[0].is_input is True
            assert devices[0].is_output is False
            assert devices[0].is_default is True
            assert devices[0].sample_rate == 48000

            assert devices[1].name == "Built-in Speakers"
            assert devices[1].is_input is False
            assert devices[1].is_output is True
            assert devices[1].is_default is True

            assert devices[2].name == "USB Audio Device"
            assert devices[2].is_input is True
            assert devices[2].is_output is True
            assert devices[2].is_default is False

    def test_list_audio_devices_empty(self) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = (None, None)

            devices = list_audio_devices()

            assert devices == []


class TestGetDefaultInputDevice:
    def test_get_default_input_device(self, mock_devices: list[dict[str, object]]) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.default.device = (0, 1)

            device = get_default_input_device()

            assert device is not None
            assert device.index == 0
            assert device.name == "Built-in Microphone"
            assert device.is_input is True
            assert device.is_default is True

    def test_get_default_input_device_none(self) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = (None, None)

            device = get_default_input_device()

            assert device is None

    def test_no_input_device_available(self) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = [
                {
                    "name": "Speakers Only",
                    "max_input_channels": 0,
                    "max_output_channels": 2,
                    "default_samplerate": 48000.0,
                }
            ]
            mock_sd.default.device = (None, None)

            device = get_default_input_device()

            assert device is None


class TestGetDefaultOutputDevice:
    def test_get_default_output_device(self, mock_devices: list[dict[str, object]]) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.default.device = (0, 1)

            device = get_default_output_device()

            assert device is not None
            assert device.index == 1
            assert device.name == "Built-in Speakers"
            assert device.is_output is True
            assert device.is_default is True


class TestResolveDevice:
    def test_resolve_device_with_none_returns_default(
        self, mock_devices: list[dict[str, object]]
    ) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.default.device = (0, 1)

            result = resolve_device(None, is_input=True)

            assert result == 0

    def test_resolve_device_with_int_returns_int(self) -> None:
        result = resolve_device(2, is_input=True)

        assert result == 2

    def test_resolve_device_with_matching_name(self, mock_devices: list[dict[str, object]]) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.default.device = (0, 1)

            result = resolve_device("USB Audio Device", is_input=True)

            assert result == 2

    def test_resolve_device_with_matching_name_case_insensitive(
        self, mock_devices: list[dict[str, object]]
    ) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.default.device = (0, 1)

            result = resolve_device("usb audio device", is_input=True)

            assert result == 2

    def test_resolve_device_with_also_name_returns_string(
        self, mock_devices: list[dict[str, object]]
    ) -> None:
        with patch("app.core.audio.devices.sd") as mock_sd:
            mock_sd.query_devices.return_value = mock_devices
            mock_sd.default.device = (0, 1)

            result = resolve_device("plughw:1,0", is_input=True)

            assert result == "plughw:1,0"
