import asyncio
from app.orchestrator.session import Session, SessionState


def test_session_initialization():
    session = Session()
    assert session.session_id is not None
    assert session.state == SessionState.IDLE
    assert isinstance(session.cancel_event, asyncio.Event)
    assert not session.cancel_event.is_set()


def test_session_state_transitions():
    session = Session()
    session.state = SessionState.LISTENING
    assert session.state == SessionState.LISTENING


def test_session_cancellation():
    session = Session()
    session.cancel_event.set()
    assert session.cancel_event.is_set()
