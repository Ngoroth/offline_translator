import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto


class SessionState(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: SessionState = SessionState.IDLE
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    source_lang: str = "English"
    target_lang: str = "Russian"
    tts_model_path: str | None = None
