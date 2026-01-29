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
                # If pipeline is active, we wait for Press OR Completion (Barge-in support)
                if self.pipeline.session:
                    input_task = asyncio.create_task(self.input.wait_for_press())
                    completion_task = asyncio.create_task(self.pipeline.wait_for_completion())

                    done, _ = await asyncio.wait(
                        [input_task, completion_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    if input_task in done:
                        # Barge-in Detected
                        role = input_task.result()
                        logger.info(f"PTT Pressed (Barge-in): {role}")

                        # Cancel completion wait
                        _ = completion_task.cancel()
                        try:
                            await completion_task
                        except asyncio.CancelledError:
                            pass

                        await self.pipeline.handle_barge_in()

                    else:
                        # Completed naturally
                        await completion_task

                        # Cleanup input task
                        _ = input_task.cancel()
                        try:
                            await input_task
                        except asyncio.CancelledError:
                            pass

                        logger.info("Transaction complete. Ready.")

                        # Now wait for next press (IDLE)
                        role = await self.input.wait_for_press()
                        logger.info(f"PTT Pressed: {role}")

                else:
                    # IDLE State
                    role = await self.input.wait_for_press()
                    logger.info(f"PTT Pressed: {role}")

                # 2. Start Session (Recording + Workers)
                _ = await self.pipeline.start_session(role)

                # 3. Wait for PTT Release
                await self.input.wait_for_release(role)
                logger.info(f"PTT Released: {role}")

                # 4. Handle Completion (Stop Rec -> STT -> LLM -> TTS -> Play)
                await self.pipeline.handle_input_complete()

                # Loop continues to handle completion or new press

        except asyncio.CancelledError:
            logger.info("Orchestrator cancelled.")
            await self.pipeline.stop_session()  # Force stop if needed
            raise
