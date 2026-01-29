from app.orchestrator.session import SessionManager, Session


def test_session_manager_start_session_params():
    """
    Test that SessionManager.start_session accepts language and voice parameters
    and returns a properly configured Session object.
    """
    manager = SessionManager()

    session = manager.start_session(source_lang="en", target_lang="ru", tts_voice="ru_voice_model")

    assert isinstance(session, Session)
    assert session.source_lang == "en"
    assert session.target_lang == "ru"
    assert session.tts_voice == "ru_voice_model"
    assert manager.is_valid(session.session_id)
