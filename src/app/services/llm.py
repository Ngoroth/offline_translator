import asyncio
import re
import time
from typing import cast, final, TYPE_CHECKING

from llama_cpp import Llama, CreateChatCompletionResponse, ChatCompletionRequestMessage
from loguru import logger

from app.core.config import LLMSettings

if TYPE_CHECKING:
    from app.orchestrator.session import SessionManager


def clean_llm_output(text: str) -> str:
    """Remove LLM reasoning tags like <think>...</think> from output."""
    # Remove <think>...</think> blocks (including multiline)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove any remaining XML-like tags
    text = re.sub(r"<[^>]+>", "", text)
    # Clean up extra whitespace
    return text.strip()


class LLMError(Exception):
    """Base exception for LLM service errors."""

    pass


class LLMModelLoadError(LLMError):
    """Raised when the model fails to load."""

    pass


@final
class LLMService:
    def __init__(
        self, settings: LLMSettings, session_manager: "SessionManager | None" = None
    ) -> None:
        self.settings = settings
        self.session_manager = session_manager
        self._model: Llama | None = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self._init_model()

    def _init_model(self) -> None:
        try:
            logger.info(f"Loading LLM model from {self.settings.model_path}")
            start_time = time.perf_counter()
            self._model = Llama(
                model_path=self.settings.model_path,
                n_ctx=self.settings.context_window,
                n_threads=self.settings.n_threads,
                n_gpu_layers=self.settings.n_gpu_layers,
                verbose=False,
            )
            load_time = time.perf_counter() - start_time
            logger.info(f"LLM model loaded in {load_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            raise LLMModelLoadError(f"Failed to load model from {self.settings.model_path}") from e

    async def translate(
        self, text: str, source_lang: str, target_lang: str, session_id: str | None = None
    ) -> str | None:
        start_time = time.perf_counter()

        if session_id and self.session_manager and not self.session_manager.is_valid(session_id):
            logger.debug(f"LLM: Pre-check cancelled for session {session_id}")
            return None

        if not self._model:
            raise LLMError("Model not initialized")

        system_prompt = (
            f"You are a translator. Translate the user's message from {source_lang} "
            f"to {target_lang}. Output ONLY the translation, nothing else."
        )

        messages: list[ChatCompletionRequestMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        try:
            # Offload blocking inference to a thread
            # Lock to prevent concurrent access to the model
            async with self._lock:
                if (
                    session_id
                    and self.session_manager
                    and not self.session_manager.is_valid(session_id)
                ):
                    logger.debug(f"LLM: Locked pre-check cancelled for session {session_id}")
                    return None

                inference_start = time.perf_counter()
                response = await asyncio.to_thread(
                    self._model.create_chat_completion,
                    messages=messages,
                    temperature=0.1,
                )
                inference_time = time.perf_counter() - inference_start
                logger.info(f"LLM inference took {inference_time:.2f}s")

            if (
                session_id
                and self.session_manager
                and not self.session_manager.is_valid(session_id)
            ):
                logger.debug(f"LLM: Post-check cancelled for session {session_id}")
                return None

            # Cast to expected response type since stream=False
            resp_typed = cast(CreateChatCompletionResponse, response)
            content = resp_typed["choices"][0]["message"]["content"]

            # Clean LLM output (remove thinking tags, etc.)
            cleaned = clean_llm_output(content) if content else ""

            total_time = time.perf_counter() - start_time
            logger.info(
                f"LLM total translate time: {total_time:.2f}s (inference: {inference_time:.2f}s)"
            )

            return cleaned

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise LLMError("Translation failed") from e
