import re

from fastapi import HTTPException, Request, Response, status

from .config import UC_USER_URL, UC_AVATAR_URL
from .http_client import client, avatar_client
from .modules.database import get_db_context
from .modules.repositories import UserRepository, SessionRepository
from .session import SESSION_COOKIE


async def fetch_avatar_url(uid: int) -> str | None:
    try:
        resp = await avatar_client.get(UC_AVATAR_URL, params={"uid": uid, "size": "big", "ts": 1})
        if resp.status_code == 302 and "location" in resp.headers:
            return resp.headers["location"]
    except Exception:
        pass
    return None


async def _resolve_user(request: Request, user_info: dict | None = None, response: Response | None = None) -> dict:
    resolved_via_fallback = False

    if user_info:
        user_id = user_info["uid"]
        username = user_info.get("username", "")
    else:
        session_id = request.cookies.get(SESSION_COOKIE)
        if session_id:
            async with get_db_context() as db:
                session = await SessionRepository.get(db, session_id)
                if session and SessionRepository.is_valid(session):
                    await SessionRepository.refresh_expiry(db, session)
                    user_id = int(session.user_id)
                    username = str(session.username)
                else:
                    if session:
                        await SessionRepository.delete(db, session_id)
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
        else:
            resolved_via_fallback = True
            sid_cookie = None
            for name in request.cookies:
                if name.startswith("OcXe_") and "_sid" in name:
                    sid_cookie = request.cookies[name]
                    break

            if not sid_cookie:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

            try:
                cookies = {k: v for k, v in request.cookies.items() if k.startswith("OcXe_")}
                resp = await client.get(
                    UC_USER_URL,
                    params={"mod": "space", "uid": "me"},
                    cookies=cookies,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                )
                uid_match = re.search(r'discuz_uid\s*=\s*[\'"](\d+)[\'"]', resp.text)

                if uid_match:
                    uid = int(uid_match.group(1))
                    if uid > 0:
                        user_id = uid
                        username_match = re.search(r'欢迎您回来，\s*([^<]+)', resp.text)
                        username = username_match.group(1).strip() if username_match else ""
                    else:
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
                else:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无法获取用户信息")
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"会话验证失败: {str(e)}")

    async with get_db_context() as db:
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            avatar_url = await fetch_avatar_url(user_id)
            try:
                user = await UserRepository.create(db, user_id, username, avatar_url)
            except Exception as e:
                if "Duplicate entry" in str(e) and "for key 'users.username'" in str(e):
                    existing = await UserRepository.get_by_username(db, username)
                    if existing:
                        if not existing.avatar_url:
                            avatar_url = await fetch_avatar_url(user_id)
                            await UserRepository.update(db, existing, id=user_id, avatar_url=avatar_url)
                        else:
                            await UserRepository.update(db, existing, id=user_id)
                        user = await UserRepository.get_by_id(db, user_id)
                else:
                    raise
        elif not user.avatar_url:
            avatar_url = await fetch_avatar_url(user_id)
            await UserRepository.update(db, user, avatar_url=avatar_url)

    if resolved_via_fallback and response:
        from .session import create_session as _create_session, SESSION_COOKIE as _COOKIE
        new_sid = await _create_session(user_id, user.username)
        response.set_cookie(
            key=_COOKIE,
            value=new_sid,
            path="/",
            httponly=True,
            samesite="lax",
            max_age=7200,
        )

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