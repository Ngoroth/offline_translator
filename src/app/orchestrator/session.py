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
    source_lang: str = "en"
    target_lang: str = "ru"
    tts_voice: str | None = None


class SessionManager:
    def __init__(self):
        self._active_sessions: set[str] = set()

    def start_session(
        self,
        source_lang: str = "en",
        target_lang: str = "ru",
        tts_voice: str | None = None,
    ) -> Session:
        session_id = str(uuid.uuid4())
        self._active_sessions.add(session_id)
        return Session(
            session_id=session_id,
            source_lang=source_lang,
            target_lang=target_lang,
            tts_voice=tts_voice,
        )

    def cancel_session(self, session_id: str) -> None:
        self._active_sessions.discard(session_id)

    def is_valid(self, session_id: str) -> bool:
        return session_id in self._active_sessions
