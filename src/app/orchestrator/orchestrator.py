import asyncio
from loguru import logger
from app.core.input import BaseInput
from app.orchestrator.pipeline import TranslationPipeline


class Orchestrator:
    pipeline: TranslationPipeline
    input: BaseInput

    def __init__(self, pipeline: TranslationPipeline, input_provider: BaseInput):
        self.pipeline = pipeline
        self.input = input_provider

    async def run(self) -> None:
        """Main Orchestrator loop."""
        logger.info("Orchestrator started. Waiting for input...")
        try:
            while True:
                # 1. Wait for PTT Press
                role = await self.input.wait_for_press()
                logger.info(f"PTT Pressed: {role}")

                # 2. Start Session (Recording + Workers)
                _ = await self.pipeline.start_session(role)

                # 3. Wait for PTT Release
                await self.input.wait_for_release(role)
                logger.info(f"PTT Released: {role}")

                # 4. Handle Completion (Stop Rec -> STT -> LLM -> TTS -> Play)
                await self.pipeline.handle_input_complete()

                # 5. Wait for everything to finish (drain queues)
                await self.pipeline.wait_for_completion()
                logger.info("Transaction complete. Ready.")

        except asyncio.CancelledError:
            logger.info("Orchestrator cancelled.")
            await self.pipeline.stop_session()  # Force stop if needed
            raise
