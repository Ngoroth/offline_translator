import pytest
import threading
import numpy as np
from unittest.mock import MagicMock, patch
from typing import Any
from app.core.audio.player import AudioPlayer


@pytest.fixture
def audio_player() -> AudioPlayer:
    return AudioPlayer(sample_rate=16000)


@patch("app.core.audio.player.sd.play")
@patch("app.core.audio.player.sd.stop")
def test_stop_clears_state_and_calls_sd_stop(
    mock_stop: MagicMock, _mock_play: MagicMock, audio_player: AudioPlayer
) -> None:
    """Test that stop() calls sd.stop() and resets state to IDLE."""
    # We expect 'state' attribute to exist and be managed.
    # Initial state should be IDLE (implied)

    # Trigger stop
    audio_player.stop()

    mock_stop.assert_called_once()
    assert hasattr(audio_player, "state")
    assert audio_player.state == "IDLE"


@patch("app.core.audio.player.sd.play")
@patch("app.core.audio.player.sd.stop")
def test_play_sets_state(
    _mock_stop: MagicMock, mock_play: MagicMock, audio_player: AudioPlayer
) -> None:
    """Test that play() sets state to PLAYING then IDLE."""
    test_data = np.zeros(1600, dtype=np.float32)

    # We want to verify it goes to PLAYING.
    # We can mock sd.play to check the state while it's "playing".

    def side_effect(*_args: Any, **_kwargs: Any) -> None:
        assert audio_player.state == "PLAYING"

    mock_play.side_effect = side_effect

    audio_player.play(test_data)

    # After play returns (blocking), it should be IDLE
    assert audio_player.state == "IDLE"


def test_stop_is_thread_safe(audio_player: AudioPlayer) -> None:
    """Test stop can be called from another thread."""
    t = threading.Thread(target=audio_player.stop)
    t.start()
    t.join()
