import asyncio
import sys
import os

# Add src to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from app.core.input import EvdevInput, Role
from loguru import logger

# Configure logger to print to stdout immediately
_ = logger.remove()
_ = logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | {message}", level="INFO")


async def test_input():
    logger.info("--- HARDWARE DIAGNOSTIC TOOL ---")

    # 1. Test Input
    device_path = "/dev/input/event1"  # Numpad
    logger.info(f"Testing Input on {device_path}...")
    logger.info("Press KP_5 or KP_6 now! (Press Ctrl+C to stop)")

    key_map: dict[Role, str] = {"a": "KEY_KP5", "b": "KEY_KP6"}

    input_handler = EvdevInput(device_path, key_map)

    # Manually start (since we are not using the Orchestrator)
    input_handler.start()

    try:
        while True:
            # Check direct press status
            if input_handler.is_pressed("a"):
                logger.info(">> BUTTON A (KP_5) IS HELD DOWN")

            if input_handler.is_pressed("b"):
                logger.info(">> BUTTON B (KP_6) IS HELD DOWN")

            # Wait for event using public API (non-blocking poll with timeout)
            try:
                role = await asyncio.wait_for(input_handler.wait_for_press(), timeout=0.1)
                logger.info(f"!! EVENT DETECTED: Role {role} PRESSED !!")
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        input_handler.stop()


if __name__ == "__main__":
    asyncio.run(test_input())
