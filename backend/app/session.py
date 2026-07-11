import uuid

from .modules.database import get_db_context, create_all_tables
from .modules.repositories import SessionRepository

SESSION_COOKIE = "bubble_session"


async def create_session(user_id: int, username: str,
                         device_info: str = None, ip_address: str = None,
                         session_id: str = None) -> str:
    if session_id is None:
        session_id = str(uuid.uuid4())
    async with get_db_context() as db:
        await SessionRepository.create(db, session_id, user_id, username,
                                       device_info, ip_address)
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


async def get_user_sessions(user_id: int) -> list[dict]:
    """获取用户所有活跃 session 列表。"""
    async with get_db_context() as db:
        sessions = await SessionRepository.list_by_user(db, user_id)
    return [
        {
            "id": s.id,
            "device_info": s.device_info or "",
            "ip_address": _mask_ip(s.ip_address) if s.ip_address else "",
            "created_at": s.created_at.isoformat() if s.created_at else "",
            "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else "",
        }
        for s in sessions
    ]


def _mask_ip(ip: str) -> str:
    """部分掩码 IP 地址的最后一节以保护隐私。"""
    parts = ip.rsplit(".", 1)
    if len(parts) == 2:
        return f"{parts[0]}.***"
    return ip


async def init_sessions_table():
    await create_all_tables()