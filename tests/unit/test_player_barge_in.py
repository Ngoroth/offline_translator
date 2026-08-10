import pytest
import threading
import asyncio
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any
from app.core.audio.player import AudioPlayer
from app.orchestrator.pipeline import TranslationPipeline
from app.orchestrator.session import SessionState


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


@pytest.mark.asyncio
async def test_player_worker_defers_listening_chunks_until_release() -> None:
    settings = MagicMock()
    settings.speakers = {
        "a": MagicMock(from_lang="en", to_lang="ru", tts_model="ru_voice"),
        "b": MagicMock(from_lang="ru", to_lang="en", tts_model="en_voice"),
    }
    settings.vad.aggressiveness = 3
    settings.vad.threshold_ms = 500
    settings.vad.auto_harvest = True
    settings.audio.sample_rate = 16000
    settings.audio.playback_during_recording = False

    recorder = MagicMock()
    recorder.sample_rate = 16000
    player = MagicMock()

    pipeline = TranslationPipeline(
        settings=settings,
        stt=AsyncMock(),
        llm=AsyncMock(),
        tts=AsyncMock(),
        recorder=recorder,
        player=player,
    )

    pipeline.session = pipeline.session_manager.start_session(
        source_lang="en", target_lang="ru", tts_voice="voice"
    )
    pipeline.session.state = SessionState.LISTENING
    worker_task = asyncio.create_task(pipeline._player_worker())

    first_chunk = np.array([0.11, 0.22], dtype=np.float32).tobytes()
    second_chunk = np.array([0.33, 0.44], dtype=np.float32).tobytes()
    await pipeline.player_queue.put(first_chunk)
    await pipeline.player_queue.put(second_chunk)
    await asyncio.sleep(0.1)

    assert pipeline.session is not None
    assert pipeline.session.state == SessionState.LISTENING
    assert player.play.call_count == 0

    pipeline.session.state = SessionState.PROCESSING

    async def wait_for_two_calls() -> None:
        while player.play.call_count < 2:
            await asyncio.sleep(0.01)

    await asyncio.wait_for(wait_for_two_calls(), timeout=1.0)

    played_chunks = [call.args[0] for call in player.play.call_args_list]
    assert np.array_equal(played_chunks[0], np.frombuffer(first_chunk, dtype=np.float32))
    assert np.array_equal(played_chunks[1], np.frombuffer(second_chunk, dtype=np.float32))

    await pipeline.player_queue.put(None)
    await asyncio.wait_for(worker_task, timeout=1.0)
