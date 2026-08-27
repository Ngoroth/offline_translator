import pytest
from pydantic import ValidationError
from app.core.config import LLMSettings


def test_llm_settings_defaults():
    # model_path is required
    settings = LLMSettings(model_path="models/test.gguf")
    assert settings.context_window == 2048
    assert settings.n_threads > 0  # Should default to something reasonable
    assert settings.seed == 1


def test_llm_settings_model_path_validation():
    # Should pass with .gguf
    LLMSettings(model_path="model.gguf")

    # Should fail with non-gguf
    with pytest.raises(ValidationError) as exc:
        LLMSettings(model_path="model.bin")
    assert "must end with .gguf" in str(exc.value)


def test_llm_settings_fields_match_requirements():
    settings = LLMSettings(model_path="model.gguf", context_window=4096, n_threads=8)
    assert settings.context_window == 4096
    assert settings.n_threads == 8
