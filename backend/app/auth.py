from fastapi import HTTPException, Request, status

from .db import get_conn
from .session import SESSION_COOKIE, get_session


def get_current_user(request: Request, user_info: dict = None) -> dict:
    if user_info:
        user_id = user_info["uid"]
        username = user_info.get("username", "")
    else:
        session_id = request.cookies.get(SESSION_COOKIE)
        if session_id:
            session_data = get_session(session_id)
            if session_data:
                user_id = session_data["user_id"]
                username = session_data["username"]
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期")
        else:
            uc_auth = request.cookies.get("uc_auth")
            if uc_auth:
                from .ucenter import decode_uc_cookie
                uc_user = decode_uc_cookie(uc_auth)
                if uc_user:
                    user_id = uc_user["uid"]
                    username = uc_user["username"]
                else:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录态")
            else:
                sid_cookie = None
                for name in request.cookies:
                    if name.startswith("OcXe_") and "_sid" in name:
                        sid_cookie = request.cookies[name]
                        break

                if not sid_cookie:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

                try:
                    from .routers.auth import UC_USER_URL
                    import httpx
                    import re

                    cookies = {k: v for k, v in request.cookies.items() if k.startswith("OcXe_")}
                    user_page = httpx.get(UC_USER_URL, params={"mod": "space", "uid": "me"}, cookies=cookies)
                    uid_match = re.search(r'discuz_uid\s*=\s*[\'"](\d+)[\'"]', user_page.text)

                    if uid_match:
                        uid = int(uid_match.group(1))
                        if uid > 0:
                            user_id = uid
                            username_match = re.search(r'欢迎您回来，\s*([^<]+)', user_page.text)
                            username = username_match.group(1).strip() if username_match else ""
                        else:
                            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
                    else:
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无法获取用户信息")
                except Exception as e:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"会话验证失败: {str(e)}")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, author_name FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
            if not row:
                try:
                    cur.execute(
                        "INSERT INTO users (id, username) VALUES (%s, %s)",
                        (user_id, username),
                    )
                    conn.commit()
                    row = {"id": user_id, "username": username, "author_name": None}
                except Exception as e:
                    if "Duplicate entry" in str(e) and "for key 'users.username'" in str(e):
                        cur.execute("SELECT id, username, author_name FROM users WHERE username=%s", (username,))
                        existing = cur.fetchone()
                        if existing:
                            cur.execute(
                                "UPDATE users SET id=%s WHERE id=%s",
                                (user_id, existing["id"]),
                            )
                            conn.commit()
                            row = {"id": user_id, "username": username, "author_name": existing.get("author_name")}
                    else:
                        raise

    return row


def public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "authorName": row.get("author_name") or "",
    }