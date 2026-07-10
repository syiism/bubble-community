import uuid
from datetime import datetime, timedelta

from .modules.database import get_db_context, create_all_tables
from .modules.repositories import SessionRepository

SESSION_COOKIE = "bubble_session"
SESSION_EXPIRE = timedelta(hours=2)


def create_session(user_id: int, username: str) -> str:
    session_id = str(uuid.uuid4())
    with get_db_context() as db:
        SessionRepository.create(db, session_id, user_id, username)
    return session_id


def get_session(session_id: str) -> dict | None:
    if not session_id:
        return None

    with get_db_context() as db:
        session = SessionRepository.get(db, session_id)

        if session and SessionRepository.is_valid(db, session):
            SessionRepository.refresh_expiry(db, session)
            return {"user_id": session.user_id, "username": session.username}

        if session and not SessionRepository.is_valid(db, session):
            SessionRepository.delete(db, session_id)

    return None


def delete_session(session_id: str):
    if session_id:
        with get_db_context() as db:
            SessionRepository.delete(db, session_id)


def init_sessions_table():
    create_all_tables()
