import uuid

from .modules.database import get_db_context, create_all_tables
from .modules.repositories import SessionRepository

SESSION_COOKIE = "bubble_session"


async def create_session(user_id: int, username: str) -> str:
    session_id = str(uuid.uuid4())
    async with get_db_context() as db:
        await SessionRepository.create(db, session_id, user_id, username)
    return session_id


async def get_session(session_id: str) -> dict | None:
    if not session_id:
        return None

    async with get_db_context() as db:
        session = await SessionRepository.get(db, session_id)

        if session and SessionRepository.is_valid(session):
            await SessionRepository.refresh_expiry(db, session)
            return {"user_id": session.user_id, "username": session.username}

        if session and not SessionRepository.is_valid(session):
            await SessionRepository.delete(db, session_id)

    return None


async def delete_session(session_id: str):
    if session_id:
        async with get_db_context() as db:
            await SessionRepository.delete(db, session_id)


async def init_sessions_table():
    await create_all_tables()