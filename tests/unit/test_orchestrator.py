import asyncio
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import Orchestrator


@pytest.fixture
def orchestrator():
    with patch("app.main.load_settings") as mock_load:
        mock_settings = MagicMock()
        mock_settings.audio.sample_rate = 16000
        mock_settings.audio.playback_during_recording = False
        mock_settings.stt.model_path = "dummy"
        mock_settings.stt.language = "en"
        mock_settings.llm.model_path = "dummy"
        mock_settings.llm.n_ctx = 2048
        mock_settings.llm.thread_count = 4
        mock_settings.tts.model_path = "dummy"
        mock_settings.input.ptt_a = "space"
        mock_settings.input.ptt_b = "alt"
        mock_settings.speakers = {
            "a": MagicMock(from_lang="English", to_lang="Russian", tts_model=None),
            "b": MagicMock(from_lang="Russian", to_lang="English", tts_model=None),
        }
        mock_load.return_value = mock_settings
        return Orchestrator()


@pytest.mark.asyncio
async def test_orchestrator_clear_queues(orchestrator):
    await orchestrator.stt_queue.put("item")
    orchestrator.clear_queues()
    assert orchestrator.stt_queue.empty()


@pytest.mark.asyncio
async def test_stt_worker_skips_old_session(orchestrator):
    mock_stt = MagicMock()
    orchestrator.current_session = 2

    await orchestrator.stt_queue.put(
        {
            "role": "a",
            "audio": np.zeros(1600),
            "session_id": 1,  # Old session
        }
    )

    # Run one iteration of stt_worker
    task = asyncio.create_task(orchestrator.stt_worker(mock_stt))
    await asyncio.sleep(0.1)
    task.cancel()

    mock_stt.transcribe.assert_not_called()
    assert orchestrator.llm_queue.empty()


@pytest.mark.asyncio
async def test_llm_worker_streaming(orchestrator):
    mock_translator = MagicMock()

    async def mock_translate_stream(*args):
        yield "Hello."
        yield " How"
        yield " are"
        yield " you?"

    mock_translator.translate_stream = mock_translate_stream
    orchestrator.current_session = 1

    await orchestrator.llm_queue.put({"role": "a", "text": "Привет", "session_id": 1})

    task = asyncio.create_task(orchestrator.llm_worker(mock_translator))

    # We expect 2 sentences in tts_queue: "Hello." and "How are you?"
    item1 = await orchestrator.tts_queue.get()
    assert item1["text"] == "Hello."

    item2 = await orchestrator.tts_queue.get()
    assert item2["text"] == "How are you?"

    task.cancel()


@pytest.mark.asyncio
async def test_playback_worker_gating(orchestrator):
    mock_player = MagicMock()
    orchestrator.settings.audio.playback_during_recording = False
    orchestrator.playback_allowed.clear()  # Simulate recording in progress
    orchestrator.current_session = 1  # Match session ID

    await orchestrator.playback_queue.put({"audio": np.zeros(1600), "session_id": 1})

    task = asyncio.create_task(orchestrator.playback_worker(mock_player))
    await asyncio.sleep(0.1)

    # Player should not have been called yet because playback is blocked
    mock_player.play.assert_not_called()

    # Allow playback
    orchestrator.playback_allowed.set()
    await asyncio.sleep(0.2)  # Give it more time


@pytest.mark.asyncio
async def test_audio_capture_skips_pure_silence(orchestrator):
    mock_recorder = MagicMock()
    mock_recorder.get_last_chunk.return_value = np.zeros(480)  # 30ms @ 16k
    mock_recorder.extract_buffer.return_value = np.zeros(8000)
    mock_recorder.stop.return_value = np.zeros(8000)

    mock_input = MagicMock()
    mock_input.wait_for_press.return_value = "a"
    # Button pressed, then released after a few iterations
    mock_input.is_pressed.side_effect = [True, True, False]

    mock_player = MagicMock()

    # Mock VAD to always return False (silence)
    with (
        patch("app.main.VADService") as mock_vad_cls,
        patch("app.main.SilenceDetector") as mock_sd_cls,
    ):
        mock_vad = mock_vad_cls.return_value
        mock_vad.is_speech.return_value = False

        mock_sd = mock_sd_cls.return_value
        # Timeout after 1 iteration
        mock_sd.is_silent_timeout.return_value = True

        task = asyncio.create_task(
            orchestrator.audio_capture_task(mock_recorder, mock_input, mock_player)
        )
        await asyncio.sleep(0.2)
        task.cancel()


@pytest.mark.asyncio
async def test_audio_capture_multi_phrase(orchestrator):
    mock_recorder = MagicMock()
    mock_recorder.get_last_chunk.return_value = np.zeros(480)
    mock_recorder.extract_buffer.return_value = np.zeros(8000)
    mock_recorder.stop.return_value = np.zeros(8000)

    mock_input = MagicMock()
    mock_input.wait_for_press.return_value = "a"
    # Pressed for many iterations
    mock_input.is_pressed.side_effect = [True] * 10 + [False]

    mock_player = MagicMock()

    with (
        patch("app.main.VADService") as mock_vad_cls,
        patch("app.main.SilenceDetector") as mock_sd_cls,
    ):
        mock_vad = mock_vad_cls.return_value
        # First 3 iterations: speech, next 3: silence, then speech again
        mock_vad.is_speech.side_effect = [
            True,
            True,
            True,
            False,
            False,
            False,
            True,
            True,
            True,
            True,
        ]

        mock_sd = mock_sd_cls.return_value
        # Timeout only at iteration 6 (when we have speech=True in segment)
        mock_sd.is_silent_timeout.side_effect = [
            False,
            False,
            False,
            False,
            False,
            True,
            False,
            False,
            False,
            False,
        ]

        task = asyncio.create_task(
            orchestrator.audio_capture_task(mock_recorder, mock_input, mock_player)
        )
        await asyncio.sleep(0.5)
        task.cancel()

    # We expect 2 items in stt_queue:
    # 1. The one from "Pause detected" (after 6 iterations)
    # 2. The final one (after button release)
    assert orchestrator.stt_queue.qsize() == 2
