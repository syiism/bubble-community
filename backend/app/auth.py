import httpx

from fastapi import HTTPException, Request, status

from .db import get_conn
from .session import SESSION_COOKIE, get_session

UC_AVATAR_URL = "https://vossc.com/uc_server/avatar.php"


def fetch_avatar_url(uid: int) -> str | None:
    try:
        resp = httpx.get(UC_AVATAR_URL, params={"uid": uid, "size": "big", "ts": 1}, follow_redirects=False)
        if resp.status_code == 302 and "location" in resp.headers:
            return resp.headers["location"]
    except Exception:
        pass
    return None


def _resolve_user(request: Request, user_info: dict | None = None) -> dict:
    if user_info:
        user_id = user_info["uid"]
        username = user_info.get("username", "")
        print(f"[DEBUG] _resolve_user: using direct user_info — uid={user_id}, username={username}")
    else:
        cookies_snapshot = dict(request.cookies)
        print(f"[DEBUG] _resolve_user: cookies={ {k:v[:20]+'...' if len(v)>20 else v for k,v in cookies_snapshot.items()} }")
        print(f"[DEBUG] _resolve_user: bubble_session={request.cookies.get(SESSION_COOKIE, 'NONE')}")
        print(f"[DEBUG] _resolve_user: uc_auth={'PRESENT' if request.cookies.get('uc_auth') else 'NONE'}")
        session_id = request.cookies.get(SESSION_COOKIE)
        if session_id:
            session_data = get_session(session_id)
            if session_data:
                user_id = session_data["user_id"]
                username = session_data["username"]
                print(f"[DEBUG] _resolve_user: SESSION AUTH — user_id={user_id}, username={username}")
            else:
                # bubble_session cookie 存在但 session 已过期/无效。
                # 不降级到 uc_auth/OcXe_* 等可能属于不同用户的 cookie，
                # 直接要求重新登录，防止身份静默切换。
                print(f"[DEBUG] _resolve_user: bubble_session PRESENT but get_session returned None — raising 401")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")

        if not session_id:
            uc_auth = request.cookies.get("uc_auth")
            if uc_auth:
                from .ucenter import decode_uc_cookie
                uc_user = decode_uc_cookie(uc_auth)
                if uc_user:
                    user_id = uc_user["uid"]
                    username = uc_user["username"]
                    print(f"[DEBUG] _resolve_user: UC_AUTH FALLBACK — uid={user_id}, username={username}")
                else:
                    print(f"[DEBUG] _resolve_user: uc_auth present but decode failed")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录态")
            else:
                sid_cookie = None
                for name in request.cookies:
                    if name.startswith("OcXe_") and "_sid" in name:
                        sid_cookie = request.cookies[name]
                        break

                if not sid_cookie:
                    print(f"[DEBUG] _resolve_user: NO AUTH COOKIES FOUND — raising 401")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

                try:
                    from .routers.auth import UC_USER_URL
                    import httpx
                    import re

                    cookies = {k: v for k, v in request.cookies.items() if k.startswith("OcXe_")}
                    print(f"[DEBUG] _resolve_user: OcXe_* FALLBACK — cookies={cookies}")
                    resp = httpx.get(
                        UC_USER_URL,
                        params={"mod": "space", "uid": "me"},
                        cookies=cookies,
                        follow_redirects=True,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    )
                    uid_match = re.search(r'discuz_uid\s*=\s*[\'"](\d+)[\'"]', resp.text)

                    if uid_match:
                        uid = int(uid_match.group(1))
                        if uid > 0:
                            user_id = uid
                            username_match = re.search(r'欢迎您回来，\s*([^<]+)', resp.text)
                            username = username_match.group(1).strip() if username_match else ""
                            print(f"[DEBUG] _resolve_user: OcXe_* FALLBACK SUCCESS — uid={uid}, username={username}")
                        else:
                            print(f"[DEBUG] _resolve_user: OcXe_* uid <= 0")
                            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
                    else:
                        print(f"[DEBUG] _resolve_user: discuz_uid NOT FOUND in vossc.com response")
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无法获取用户信息")
                except Exception as e:
                    print(f"[DEBUG] _resolve_user: OcXe_* validation failed: {e}")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"会话验证失败: {str(e)}")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, author_name, avatar_url FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
            print(f"[DEBUG] DB lookup: user_id={user_id}, found={row is not None}, row={row}")
            if not row:
                avatar_url = fetch_avatar_url(user_id)
                print(f"[DEBUG] Inserting new user, avatar_url={avatar_url}")
                try:
                    cur.execute(
                        "INSERT INTO users (id, username, avatar_url) VALUES (%s, %s, %s)",
                        (user_id, username, avatar_url),
                    )
                    conn.commit()
                    row = {"id": user_id, "username": username, "author_name": None, "avatar_url": avatar_url}
                except Exception as e:
                    if "Duplicate entry" in str(e) and "for key 'users.username'" in str(e):
                        cur.execute("SELECT id, username, author_name, avatar_url FROM users WHERE username=%s", (username,))
                        existing = cur.fetchone()
                        if existing:
                            if not existing.get("avatar_url"):
                                avatar_url = fetch_avatar_url(user_id)
                                cur.execute("UPDATE users SET id=%s, avatar_url=%s WHERE id=%s", (user_id, avatar_url, existing["id"]))
                            else:
                                cur.execute("UPDATE users SET id=%s WHERE id=%s", (user_id, existing["id"]))
                            conn.commit()
                            row = {"id": user_id, "username": username, "author_name": existing.get("author_name"), "avatar_url": existing.get("avatar_url") or avatar_url}
                    else:
                        raise
            elif not row.get("avatar_url"):
                avatar_url = fetch_avatar_url(user_id)
                print(f"[DEBUG] Updating avatar_url for user {user_id}: {avatar_url}")
                cur.execute("UPDATE users SET avatar_url=%s WHERE id=%s", (avatar_url, user_id))
                conn.commit()
                row["avatar_url"] = avatar_url
            else:
                print(f"[DEBUG] User {user_id} already has avatar_url")

    return row


def get_current_user(request: Request) -> dict:
    """FastAPI dependency — resolves user without consuming the request body."""
    return _resolve_user(request)


def public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "authorName": row.get("author_name") or "",
        "avatarUrl": row.get("avatar_url") or "",
    }