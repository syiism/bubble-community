import hashlib
import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status

from .config import JWT_SECRET, JWT_EXPIRE_DAYS
from .redis_client import get_redis

TOKEN_COOKIE = "bubble_token"
TOKEN_MAX_AGE = int(timedelta(days=JWT_EXPIRE_DAYS).total_seconds())

_log = logging.getLogger("auth")

REDIS_KEY_PREFIX = "bubble_tokens"


def _device_key(uid: int, ip: str, ua: str) -> str:
    """基于用户 ID + IP + User-Agent 生成设备标识。"""
    raw = f"{uid}:{ip}:{ua}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _create_jwt(uid: int, username: str, sid: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "uid": uid,
        "username": username,
        "sid": sid,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def create_token(uid: int, username: str, sid: str) -> str:
    """创建 JWT，写入 Redis Hash（多设备支持），返回 token 字符串。"""
    token = _create_jwt(uid, username, sid)
    redis = get_redis()
    key = f"{REDIS_KEY_PREFIX}:{uid}"
    await redis.hset(key, sid, token)
    await redis.expire(key, timedelta(days=JWT_EXPIRE_DAYS))
    _log.info("Token created for uid=%s sid=%s", uid, sid)
    return token


async def delete_token(uid: int, sid: str) -> None:
    """从 Redis Hash 删除指定设备 session 的 token。"""
    redis = get_redis()
    await redis.hdel(f"{REDIS_KEY_PREFIX}:{uid}", sid)
    _log.info("Token deleted for uid=%s sid=%s", uid, sid)


async def delete_all_tokens(uid: int) -> None:
    """从 Redis 删除该用户的所有 token，全部设备注销。"""
    redis = get_redis()
    await redis.delete(f"{REDIS_KEY_PREFIX}:{uid}")
    _log.info("All tokens deleted for uid=%s", uid)


async def list_user_sessions(uid: int) -> list[str]:
    """返回用户在 Redis 中的所有活跃设备 key 列表。"""
    redis = get_redis()
    keys = await redis.hkeys(f"{REDIS_KEY_PREFIX}:{uid}")
    return keys


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
    sid = payload.get("sid", "")

    # 验证 Redis Hash 中该设备的 token 与 cookie 一致（多设备支持）
    redis = get_redis()
    key = f"{REDIS_KEY_PREFIX}:{uid}"

    if sid:
        stored = await redis.hget(key, sid)
    else:
        # 兼容旧 token（无 sid）：尝试旧 key 格式
        stored = await redis.get(f"bubble_token_{uid}")
        if stored == token:
            # 旧 token 有效，基于当前请求信息迁移到新格式
            client_ip = request.client.host if request.client else ""
            ua = request.headers.get("User-Agent", "")
            new_sid = _device_key(uid, client_ip, ua)
            await redis.hset(key, new_sid, token)
            await redis.expire(key, timedelta(days=JWT_EXPIRE_DAYS))
            await redis.delete(f"bubble_token_{uid}")
            _log.info("Migrated old token for uid=%s to device key %s", uid, new_sid)
            sid = new_sid
            stored = token

    if stored != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效，请重新登录")

    # 获取或创建用户记录
    from .modules.database import get_db_context
    from .modules.repositories import UserRepository

    async with get_db_context() as db:
        user = await UserRepository.get_or_create(db, uid, username, None)

    # 更新 session 最后活跃时间
    if sid:
        try:
            from .modules.database import get_db_context as _get_db
            from .modules.repositories import SessionRepository
            async with _get_db() as db:
                await SessionRepository.touch(db, sid)
        except Exception:
            pass  # session touch 失败不影响请求

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
