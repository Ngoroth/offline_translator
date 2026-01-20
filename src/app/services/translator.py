from typing import cast
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
import asyncio
from llama_cpp import Llama, CreateChatCompletionStreamResponse, CreateChatCompletionResponse


class TranslatorService:
    llm: Llama

    def __init__(
        self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = 0, thread_count: int = 4
    ):
        """
        Initialize the Llama model for translation.
        """
        # Convert to absolute path for Windows compatibility
        abs_model_path = str(Path(model_path).absolute())
        self.llm = Llama(
            model_path=abs_model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_threads=thread_count,
            verbose=False,
        )

    def translate(self, text: str, from_lang: str, to_lang: str) -> str:
        """
        Translate text from one language to another (blocking, batch).
        """
        system_prompt = (
            "You are a professional real-time translator. "
            f"Translate the following text from {from_lang} to {to_lang}. "
            "Output ONLY the translated text without any explanations, notes, or quotes."
        )

        raw_response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=512,
            stream=False,
        )

        resp = cast(CreateChatCompletionResponse, raw_response)
        choices = resp["choices"]
        first_choice = choices[0]
        message = first_choice["message"]
        content = message["content"]
        return str(content).strip()

    async def translate_stream(self, text: str, from_lang: str, to_lang: str) -> AsyncIterator[str]:
        """
        Translate text from one language to another with token streaming.
        Yields tokens as they are generated.
        """
        system_prompt = (
            "You are a professional real-time translator. "
            f"Translate the following text from {from_lang} to {to_lang}. "
            "Output ONLY the translated text without any explanations, notes, or quotes."
        )

        def get_iter() -> Iterator[CreateChatCompletionStreamResponse]:
            raw_resp = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.1,
                max_tokens=512,
                stream=True,
            )
            return cast(Iterator[CreateChatCompletionStreamResponse], raw_resp)

        response_iter = await asyncio.to_thread(get_iter)
        it = response_iter

        def get_next() -> tuple[CreateChatCompletionStreamResponse | None, bool]:
            try:
                return next(it), False
            except StopIteration:
                return None, True

        while True:
            chunk, is_done = await asyncio.to_thread(get_next)
            if is_done:
                break

            if chunk:
                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    content = delta["content"]
                    if content is not None:
                        yield content
