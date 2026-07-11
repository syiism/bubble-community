import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status

from .config import JWT_SECRET, JWT_EXPIRE_DAYS
from .redis_client import get_redis

TOKEN_COOKIE = "bubble_token"
TOKEN_MAX_AGE = int(timedelta(days=JWT_EXPIRE_DAYS).total_seconds())

_log = logging.getLogger("auth")


def _create_jwt(uid: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "uid": uid,
        "username": username,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def create_token(uid: int, username: str) -> str:
    """创建 JWT，写入 Redis，返回 token 字符串。"""
    token = _create_jwt(uid, username)
    redis = get_redis()
    await redis.setex(f"bubble_token_{uid}", timedelta(days=JWT_EXPIRE_DAYS), token)
    _log.info("Token created for uid=%s", uid)
    return token


async def delete_token(uid: int) -> None:
    """从 Redis 删除 token，立即注销。"""
    redis = get_redis()
    await redis.delete(f"bubble_token_{uid}")
    _log.info("Token deleted for uid=%s", uid)


def _decode_jwt(token: str) -> dict:
    """解码 JWT，验证签名和过期时间。"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证")


async def _resolve_user(request: Request) -> dict:
    token = request.cookies.get(TOKEN_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    payload = _decode_jwt(token)
    uid = payload["uid"]
    username = payload.get("username", "")

    # 验证 Redis 中的 token 与 cookie 一致（支持退出登录后立即失效）
    redis = get_redis()
    stored = await redis.get(f"bubble_token_{uid}")
    if stored != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效，请重新登录")

    # 获取或创建用户记录
    from .modules.database import get_db_context
    from .modules.repositories import UserRepository

    async with get_db_context() as db:
        user = await UserRepository.get_or_create(db, uid, username, None)

    return {
        "id": user.id,
        "username": user.username,
        "author_name": user.author_name,
        "avatar_url": user.avatar_url,
        "role": user.role or "user",
    }


async def get_current_user(request: Request) -> dict:
    return await _resolve_user(request)


# 向后兼容：部分路由曾使用不带 response 参数的版本
get_current_user_strict = get_current_user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "authorName": row.get("author_name") or "",
        "avatarUrl": row.get("avatar_url") or "",
        "role": row.get("role") or "user",
    }
