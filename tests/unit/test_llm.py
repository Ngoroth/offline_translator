import pytest
from unittest.mock import MagicMock, patch
from app.core.config import LLMSettings
from app.services.llm import LLMService, LLMError, LLMModelLoadError


from collections.abc import Generator


# Mock settings
@pytest.fixture
def mock_settings() -> LLMSettings:
    return LLMSettings(model_path="models/test.gguf", context_window=2048, n_threads=4)


# Mock Llama class
@pytest.fixture
def mock_llama() -> Generator[MagicMock, None, None]:
    with patch("app.services.llm.Llama") as mock:
        yield mock


@pytest.mark.asyncio
async def test_llm_initialization(mock_settings: LLMSettings, mock_llama: MagicMock) -> None:
    service = LLMService(mock_settings)
    # Model should be loaded
    assert getattr(service, "_model") is not None
    mock_llama.assert_called_once_with(
        model_path=mock_settings.model_path,
        n_ctx=mock_settings.context_window,
        n_threads=mock_settings.n_threads,
        n_gpu_layers=-1,
        verbose=False,
    )


@pytest.mark.asyncio
async def test_llm_initialization_failure(
    mock_settings: LLMSettings, mock_llama: MagicMock
) -> None:
    mock_llama.side_effect = Exception("Model load failed")
    with pytest.raises(LLMModelLoadError):
        LLMService(mock_settings)


@pytest.mark.asyncio
async def test_translate_success(mock_settings: LLMSettings, mock_llama: MagicMock) -> None:
    service = LLMService(mock_settings)

    # Mock create_chat_completion response
    mock_response = {"choices": [{"message": {"content": "Translated text"}}]}

    # We need to configure the instance returned by the class constructor
    mock_instance = mock_llama.return_value
    mock_instance.create_chat_completion.return_value = mock_response

    result = await service.translate("Hello", "en", "es")

    assert result == "Translated text"

    # Verify call on the instance
    mock_instance.create_chat_completion.assert_called_once()

    # Verify prompt structure
    call_args = mock_instance.create_chat_completion.call_args
    assert call_args.kwargs["messages"][0]["role"] == "system"
    assert "interpreter" in call_args.kwargs["messages"][0]["content"]
    assert call_args.kwargs["messages"][1]["role"] == "user"
    assert call_args.kwargs["messages"][1]["content"] == "Hello"


@pytest.mark.asyncio
async def test_translate_failure(mock_settings: LLMSettings, mock_llama: MagicMock) -> None:
    service = LLMService(mock_settings)

    mock_instance = mock_llama.return_value
    mock_instance.create_chat_completion.side_effect = Exception("Inference failed")

    with pytest.raises(LLMError):
        await service.translate("Hello", "en", "es")


@pytest.mark.asyncio
async def test_translate_cancelled(mock_settings: LLMSettings, mock_llama: MagicMock) -> None:
    mock_session_manager = MagicMock()
    mock_session_manager.is_valid.return_value = False

    service = LLMService(mock_settings, session_manager=mock_session_manager)

    result = await service.translate("Hello", "en", "es", session_id="abc")
    assert result is None

    # Verify inference not called
    mock_llama.return_value.create_chat_completion.assert_not_called()
