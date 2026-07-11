from fastapi import APIRouter, Depends, HTTPException, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth import get_current_user, public_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


@router.get("/check-username")
async def check_username(username: str):
    if not username.strip():
        raise HTTPException(status_code=400, detail="用户名不能为空")

    from ..modules.database import get_db_context
    from ..modules.repositories import UserRepository

    async with get_db_context() as db:
        user = await UserRepository.get_by_username(db, username)
    return {"code": 0, "available": user is None}


@router.post("/register")
async def register(request: Request, response: Response):
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "")
        password2 = body.get("password2", "")

        if not username:
            raise HTTPException(status_code=400, detail="用户名不能为空")
        if password and len(password) < 6:
            raise HTTPException(status_code=400, detail="密码长度不能少于 6 个字符")
        if password != password2:
            raise HTTPException(status_code=400, detail="两次输入的密码不一致")

        from ..modules.database import get_db_context
        from ..modules.repositories import UserRepository
        from ..password_util import hash_password
        from ..auth import create_token, TOKEN_COOKIE, TOKEN_MAX_AGE, _device_key
        from ..session import create_session

        async with get_db_context() as db:
            existing = await UserRepository.get_by_username(db, username)
            if existing:
                raise HTTPException(status_code=409, detail="该用户名已注册")

            # 获取当前最大用户 ID 并 +1 作为新 ID
            from sqlalchemy import func, select
            from ..modules.user import User
            max_id = await db.execute(select(func.max(User.id)))
            uid = (max_id.scalar() or 0) + 1

            hashed = hash_password(password) if password else None
            new_user = User(id=uid, username=username, password=hashed)
            db.add(new_user)
            await db.commit()

        device_info = request.headers.get("User-Agent", "")
        client_ip = request.client.host if request.client else ""
        session_id = _device_key(uid, client_ip, device_info)

        token = await create_token(uid, username, session_id)
        await create_session(uid, username, device_info, client_ip,
                             session_id=session_id)

        response.set_cookie(
            key=TOKEN_COOKIE,
            value=token,
            path="/",
            httponly=True,
            samesite="lax",
            max_age=TOKEN_MAX_AGE,
        )

        return {
            "code": 0,
            "message": "注册成功",
            "user": {
                "id": uid,
                "username": username,
                "authorName": "",
                "avatarUrl": "",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"注册异常: {str(e)}"
        )


@router.post("/login")
async def login(request: Request, response: Response):
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "")

        if not username:
            raise HTTPException(status_code=400, detail="用户名不能为空")

        from ..modules.database import get_db_context
        from ..modules.repositories import UserRepository
        from ..password_util import check_password

        async with get_db_context() as db:
            user = await UserRepository.get_by_username(db, username)

        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 如果用户有密码则校验，无密码（旧账户）允许登录
        if user.password:
            if not password:
                raise HTTPException(status_code=401, detail="用户名或密码错误")
            if not check_password(password, user.password):
                raise HTTPException(status_code=401, detail="用户名或密码错误")

        user_id = user.id
        resolved_username = user.username

        from ..auth import create_token, TOKEN_COOKIE, TOKEN_MAX_AGE, _device_key
        from ..session import create_session

        # 基于 IP + User-Agent 生成设备标识（多设备支持）
        device_info = request.headers.get("User-Agent", "")
        client_ip = request.client.host if request.client else ""
        session_id = _device_key(user_id, client_ip, device_info)

        token = await create_token(user_id, resolved_username, session_id)
        await create_session(user_id, resolved_username, device_info, client_ip,
                             session_id=session_id)

        response.set_cookie(
            key=TOKEN_COOKIE,
            value=token,
            path="/",
            httponly=True,
            samesite="lax",
            max_age=TOKEN_MAX_AGE,
        )

        import logging
        _log = logging.getLogger("auth")
        _log.info(
            "[login] user=%s uid=%s sid=%s ip=%s",
            username, user_id, session_id, client_ip,
        )

        return {
            "code": 0,
            "message": "登录成功",
            "user": {
                "id": user.id,
                "username": user.username,
                "authorName": user.author_name or "",
                "avatarUrl": user.avatar_url or "",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录异常: {str(e)}")


@router.post("/forget")
async def forget_password(request: Request, user=Depends(get_current_user)):
    try:
        body = await request.json()
        new_password = body.get("new_password", "")
        confirm_password = body.get("confirm_password", "")

        if not new_password:
            raise HTTPException(status_code=400, detail="新密码不能为空")
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="密码长度不能少于 6 个字符")
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="两次输入的密码不一致")

        from ..modules.database import get_db_context
        from ..modules.repositories import UserRepository

        async with get_db_context() as db:
            await UserRepository.update_password(db, user["id"], new_password)

        return {"code": 0, "message": "密码设置成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"密码设置异常: {str(e)}")


@router.get("/me")
async def me(user=Depends(get_current_user), response: Response = None):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return {"user": public_user(user)}


@router.post("/logout")
async def logout(request: Request, response: Response):
    from ..auth import TOKEN_COOKIE, delete_token, _decode_jwt
    from ..session import delete_session
    token = request.cookies.get(TOKEN_COOKIE)
    if token:
        try:
            payload = _decode_jwt(token)
            uid = payload["uid"]
            sid = payload.get("sid", "")
            if sid:
                await delete_token(uid, sid)
                await delete_session(sid)
            else:
                # 兼容旧 token（无 sid）
                await delete_token(uid, "")
        except Exception:
            pass
    response.delete_cookie(TOKEN_COOKIE, path="/")
    return {"code": 0, "message": "退出成功"}


@router.get("/sessions")
async def list_my_sessions(request: Request, user=Depends(get_current_user)):
    """列出当前用户的所有活跃会话。"""
    from ..session import get_user_sessions
    from ..auth import _decode_jwt, TOKEN_COOKIE

    sessions = await get_user_sessions(user["id"])
    current_sid = ""
    token = request.cookies.get(TOKEN_COOKIE)
    if token:
        try:
            payload = _decode_jwt(token)
            current_sid = payload.get("sid", "")
        except Exception:
            pass

    return {
        "code": 0,
        "sessions": [
            {**s, "is_current": s["id"] == current_sid}
            for s in sessions
        ],
    }


@router.post("/sessions/revoke")
async def revoke_session(request: Request, user=Depends(get_current_user)):
    """撤销指定 session（远程注销设备）。"""
    try:
        body = await request.json()
        session_id = body.get("session_id", "")
    except Exception:
        raise HTTPException(status_code=400, detail="请求格式错误")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")

    from ..auth import _decode_jwt, TOKEN_COOKIE, delete_token
    from ..session import delete_session

    # 防止撤销当前设备
    token = request.cookies.get(TOKEN_COOKIE)
    if token:
        try:
            payload = _decode_jwt(token)
            if payload.get("sid") == session_id:
                raise HTTPException(status_code=400, detail="不能撤销当前设备，请使用退出登录")
        except HTTPException:
            raise
        except Exception:
            pass

    await delete_token(user["id"], session_id)
    try:
        await delete_session(session_id)
    except Exception:
        pass

    return {"code": 0, "message": "已撤销该设备"}


@router.post("/sessions/logout-all")
async def logout_all_devices(request: Request, user=Depends(get_current_user)):
    """退出所有其他设备，保留当前设备。"""
    from datetime import timedelta
    from ..auth import _decode_jwt, TOKEN_COOKIE, delete_all_tokens
    from ..config import JWT_EXPIRE_DAYS
    from ..modules.database import get_db_context
    from ..modules.repositories import SessionRepository
    from ..redis_client import get_redis

    current_sid = ""
    token = request.cookies.get(TOKEN_COOKIE)
    if token:
        try:
            payload = _decode_jwt(token)
            current_sid = payload.get("sid", "")
        except Exception:
            pass

    # 删除所有 Redis token
    await delete_all_tokens(user["id"])

    # 删除所有 DB session
    async with get_db_context() as db:
        await SessionRepository.delete_by_user(db, user["id"])

    # 重新注册当前 session
    if current_sid and token:
        redis = get_redis()
        key = f"bubble_tokens:{user['id']}"
        await redis.hset(key, current_sid, token)
        await redis.expire(key, timedelta(days=JWT_EXPIRE_DAYS))

    return {"code": 0, "message": "其他设备已全部退出"}