from fastapi import HTTPException, Request, Response, status

from .modules.database import get_db_context
from .modules.repositories import UserRepository, SessionRepository
from .session import SESSION_COOKIE


async def _resolve_user(request: Request, user_info: dict | None = None, response: Response | None = None) -> dict:

    if user_info:
        user_id = user_info["uid"]
        username = user_info.get("username", "")
        async with get_db_context() as db:
            user = await UserRepository.get_or_create(db, user_id, username, None)
    else:
        session_id = request.cookies.get(SESSION_COOKIE)
        if not session_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

        async with get_db_context() as db:
            # 带行锁读取 session，避免并发刷新/删除竞态
            session = await SessionRepository.get_for_update(db, session_id)
            if not session or not SessionRepository.is_valid(session):
                if session:
                    await SessionRepository.delete(db, session_id)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")

            user_id = int(session.user_id)
            username = str(session.username)
            await SessionRepository.refresh_expiry(db, session)

            # 同一事务内完成用户查询/创建
            user = await UserRepository.get_or_create(db, user_id, username, None)

    return {
        "id": user.id,
        "username": user.username,
        "author_name": user.author_name,
        "avatar_url": user.avatar_url,
    }


async def get_current_user(request: Request, response: Response) -> dict:
    return await _resolve_user(request, response=response)


async def get_current_user_strict(request: Request) -> dict:
    return await _resolve_user(request)


def public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "authorName": row.get("author_name") or "",
        "avatarUrl": row.get("avatar_url") or "",
    }