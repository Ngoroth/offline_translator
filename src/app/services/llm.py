import asyncio
from typing import cast, final

from llama_cpp import Llama, CreateChatCompletionResponse, ChatCompletionRequestMessage
from loguru import logger

from app.core.config import LLMSettings


class LLMError(Exception):
    """Base exception for LLM service errors."""

    pass


class LLMModelLoadError(LLMError):
    """Raised when the model fails to load."""

    pass


@final
class LLMService:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        self._model: Llama | None = None
        self._init_model()

    def _init_model(self) -> None:
        try:
            logger.info(f"Loading LLM model from {self.settings.model_path}")
            self._model = Llama(
                model_path=self.settings.model_path,
                n_ctx=self.settings.context_window,
                n_threads=self.settings.n_threads,
                n_gpu_layers=self.settings.n_gpu_layers,
                verbose=False,
            )
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            raise LLMModelLoadError(f"Failed to load model from {self.settings.model_path}") from e

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not self._model:
            raise LLMError("Model not initialized")

        system_prompt = (
            f"You are a helpful simultaneous interpreter from {source_lang} to {target_lang}. "
            "Translate the user input directly. Do not add explanations."
        )

        messages: list[ChatCompletionRequestMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        try:
            # Offload blocking inference to a thread
            response = await asyncio.to_thread(
                self._model.create_chat_completion,
                messages=messages,
                temperature=0.1,
            )

            # Cast to expected response type since stream=False
            resp_typed = cast(CreateChatCompletionResponse, response)
            content = resp_typed["choices"][0]["message"]["content"]

            return content.strip() if content else ""

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise LLMError("Translation failed") from e
