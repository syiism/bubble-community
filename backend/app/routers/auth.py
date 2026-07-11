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
        from ..auth import create_token, TOKEN_COOKIE, TOKEN_MAX_AGE

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

        token = await create_token(uid, username)
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

        from ..auth import create_token, delete_token, TOKEN_COOKIE, TOKEN_MAX_AGE

        # 如果已登录，先清除旧 token（单设备登录）
        old_token = request.cookies.get(TOKEN_COOKIE)
        if old_token:
            try:
                import jwt
                from ..config import JWT_SECRET
                old_payload = jwt.decode(old_token, JWT_SECRET, algorithms=["HS256"])
                await delete_token(old_payload["uid"])
            except Exception:
                pass

        token = await create_token(user_id, resolved_username)
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
            "[login] user=%s uid=%s",
            username, user_id,
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
    from ..auth import TOKEN_COOKIE, delete_token
    token = request.cookies.get(TOKEN_COOKIE)
    if token:
        try:
            import jwt
            from ..config import JWT_SECRET
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            await delete_token(payload["uid"])
        except Exception:
            pass
    response.delete_cookie(TOKEN_COOKIE, path="/")
    return {"code": 0, "message": "退出成功"}