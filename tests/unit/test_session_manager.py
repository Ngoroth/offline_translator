import pytest
import asyncio
from app.orchestrator.session import SessionManager


@pytest.fixture
def session_manager():
    return SessionManager()


def test_start_session(session_manager):
    session_id = session_manager.start_session()
    assert isinstance(session_id, str)
    assert len(session_id) > 0
    assert session_manager.is_valid(session_id)


def test_cancel_session(session_manager):
    session_id = session_manager.start_session()
    assert session_manager.is_valid(session_id)

    session_manager.cancel_session(session_id)
    assert not session_manager.is_valid(session_id)


def test_is_valid_unknown_session(session_manager):
    assert not session_manager.is_valid("unknown-id")


def test_multiple_sessions(session_manager):
    sid1 = session_manager.start_session()
    sid2 = session_manager.start_session()

    # Both could be valid if we support concurrent sessions,
    # OR start_session implicitly cancels previous.
    # Story implies "surgically cancel" so maybe multiple are tracked?
    # "track unique session IDs for every interaction"
    # For now, assume independent validity unless logic dictates otherwise.

    assert session_manager.is_valid(sid1)
    assert session_manager.is_valid(sid2)

    session_manager.cancel_session(sid1)
    assert not session_manager.is_valid(sid1)
    assert session_manager.is_valid(sid2)
