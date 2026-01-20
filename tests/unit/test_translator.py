from unittest.mock import patch
from app.services.translator import TranslatorService


@patch("app.services.translator.Llama")
def test_translator_translate(mock_llama):
    """Test that TranslatorService uses LLM to translate text."""
    # Setup mock model
    mock_model_instance = mock_llama.return_value
    mock_model_instance.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "Привет, мир"}}]
    }

    translator = TranslatorService(model_path="models/llm/test.gguf")

    result = translator.translate("Hello world", from_lang="English", to_lang="Russian")

    assert result == "Привет, мир"
    mock_model_instance.create_chat_completion.assert_called_once()

    # Check if prompt contains the languages
    args, kwargs = mock_model_instance.create_chat_completion.call_args
    messages = kwargs.get("messages")
    assert any("English" in m["content"] for m in messages)
    assert any("Russian" in m["content"] for m in messages)
    assert any("Hello world" in m["content"] for m in messages)
