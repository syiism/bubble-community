import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status

from .config import JWT_SECRET, JWT_EXPIRE_DAYS, COOKIE_SECURE, COOKIE_SAMESITE
from .redis_client import get_redis

TOKEN_COOKIE = "bubble_community_token"
TOKEN_COOKIE_PATH = "/"
TOKEN_MAX_AGE = int(timedelta(days=JWT_EXPIRE_DAYS).total_seconds())

_log = logging.getLogger("auth")


def set_auth_cookie(response, token: str) -> None:
    """Set JWT auth cookie (env-driven Secure/SameSite for local HTTP vs prod HTTPS)."""
    response.set_cookie(
        key=TOKEN_COOKIE,
        value=token,
        path=TOKEN_COOKIE_PATH,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        max_age=TOKEN_MAX_AGE,
    )


def clear_auth_cookie(response) -> None:
    response.delete_cookie(
        key=TOKEN_COOKIE,
        path=TOKEN_COOKIE_PATH,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
    )

REDIS_KEY_PREFIX = "bubble_tokens"
_USER_CACHE_PREFIX = "user_info"


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


def _session_data(token: str, device_info: str, ip: str) -> str:
    """序列化 session 元数据为 JSON，与 token 一起存入 Redis。"""
    now = datetime.now(timezone.utc).isoformat()
    return json.dumps({
        "token": token,
        "device_info": device_info or "",
        "ip": ip or "",
        "created_at": now,
        "last_seen_at": now,
    }, ensure_ascii=False)


def _parse_session(raw: str | None) -> dict | None:
    """解析 Redis 中存储的 session JSON。"""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # 兼容旧格式（纯 token 字符串）
        return {"token": raw, "device_info": "", "ip": "", "created_at": "", "last_seen_at": ""}


async def create_token(uid: int, username: str, sid: str,
                       device_info: str = "", ip: str = "") -> str:
    """创建 JWT，连同设备信息写入 Redis Hash。返回 token 字符串。"""
    token = _create_jwt(uid, username, sid)
    redis = get_redis()
    key = f"{REDIS_KEY_PREFIX}:{uid}"
    await redis.hset(key, sid, _session_data(token, device_info, ip))
    await redis.expire(key, timedelta(days=JWT_EXPIRE_DAYS))
    _log.info("Token created for uid=%s sid=%s", uid, sid)
    return token


async def delete_token(uid: int, sid: str) -> None:
    """从 Redis Hash 删除指定设备的 session。"""
    redis = get_redis()
    await redis.hdel(f"{REDIS_KEY_PREFIX}:{uid}", sid)
    _log.info("Token deleted for uid=%s sid=%s", uid, sid)


async def delete_all_tokens(uid: int) -> None:
    """从 Redis 删除该用户的所有 token，全部设备注销。"""
    redis = get_redis()
    await redis.delete(f"{REDIS_KEY_PREFIX}:{uid}")
    _log.info("All tokens deleted for uid=%s", uid)


async def get_user_sessions(uid: int) -> list[dict]:
    """返回用户所有活跃设备 session 列表（从 Redis 读取）。"""
    redis = get_redis()
    raw = await redis.hgetall(f"{REDIS_KEY_PREFIX}:{uid}")
    result = []
    for sid, data in raw.items():
        session = _parse_session(data)
        if session:
            result.append({
                "id": sid,
                "device_info": session.get("device_info", ""),
                "ip_address": session.get("ip", ""),
                "created_at": session.get("created_at", ""),
                "last_seen_at": session.get("last_seen_at", ""),
            })
    result.sort(key=lambda s: s.get("last_seen_at", ""), reverse=True)
    return result


async def touch_session(uid: int, sid: str) -> None:
    """更新 session 的最后活跃时间。"""
    redis = get_redis()
    raw = await redis.hget(f"{REDIS_KEY_PREFIX}:{uid}", sid)
    if raw:
        session = _parse_session(raw)
        if session:
            session["last_seen_at"] = datetime.now(timezone.utc).isoformat()
            await redis.hset(f"{REDIS_KEY_PREFIX}:{uid}", sid,
                             json.dumps(session, ensure_ascii=False))


def _decode_jwt(token: str) -> dict:
    """解码 JWT，验证签名和过期时间。"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的登录凭证")


def _user_info_from_db(user) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "author_name": user.author_name,
        "avatar_url": user.avatar_url,
        "role": user.role or "user",
        "is_blocked": bool(user.is_blocked) if hasattr(user, 'is_blocked') else False,
    }


async def _get_cached_user(uid: int) -> dict | None:
    redis = get_redis()
    raw = await redis.get(f"{_USER_CACHE_PREFIX}:{uid}")
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


async def _cache_user_info(uid: int, info: dict) -> None:
    redis = get_redis()
    await redis.setex(f"{_USER_CACHE_PREFIX}:{uid}", 3600, json.dumps(info, ensure_ascii=False))


async def invalidate_user_cache(uid: int) -> None:
    redis = get_redis()
    await redis.delete(f"{_USER_CACHE_PREFIX}:{uid}")
    _log.debug("User cache invalidated for uid=%s", uid)


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def _token_candidates(request: Request) -> list[tuple[str, str]]:
    """
    Ordered auth candidates: Bearer first (WebView-safe), then cookie.
    Stale cookies in WebView must not override a valid Bearer token.
    """
    out: list[tuple[str, str]] = []
    bearer = _bearer_token(request)
    if bearer:
        out.append(("bearer", bearer))
    cookie = request.cookies.get(TOKEN_COOKIE)
    if cookie and cookie not in {t for _, t in out}:
        out.append(("cookie", cookie))
    return out


async def _validate_session_token(token: str, request: Request) -> dict | None:
    """Return user_info if JWT+Redis session is valid; else None (do not raise)."""
    try:
        payload = _decode_jwt(token)
    except HTTPException:
        return None
    except Exception:
        return None

    uid = payload["uid"]
    username = payload.get("username", "")
    sid = payload.get("sid", "")

    redis = get_redis()
    key = f"{REDIS_KEY_PREFIX}:{uid}"

    if sid:
        raw = await redis.hget(key, sid)
        session = _parse_session(raw)
        stored = session["token"] if session else None
    else:
        # 兼容旧 token（无 sid）
        stored = await redis.get(f"bubble_token_{uid}")
        if stored == token:
            client_ip = request.client.host if request.client else ""
            ua = request.headers.get("User-Agent", "")
            new_sid = _device_key(uid, client_ip, ua)
            await redis.hset(key, new_sid, _session_data(token, ua, client_ip))
            await redis.expire(key, timedelta(days=JWT_EXPIRE_DAYS))
            await redis.delete(f"bubble_token_{uid}")
            _log.info("Migrated old token for uid=%s to device key %s", uid, new_sid)
            sid = new_sid
            stored = token

    if stored != token:
        return None

    user_info = await _get_cached_user(uid)
    if user_info is None:
        from .modules.database import get_db_context
        from .modules.repositories import UserRepository

        async with get_db_context() as db:
            user = await UserRepository.get_or_create(db, uid, username, None)
        user_info = _user_info_from_db(user)
        await _cache_user_info(uid, user_info)

    if user_info.get("is_blocked"):
        if sid:
            await delete_token(uid, sid)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号已被封禁")

    if sid:
        try:
            await touch_session(uid, sid)
        except Exception:
            pass

    return user_info


async def _resolve_user(request: Request) -> dict:
    candidates = _token_candidates(request)
    if not candidates:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")

    last_err = "登录已失效，请重新登录"
    for source, token in candidates:
        try:
            user_info = await _validate_session_token(token, request)
        except HTTPException as e:
            # blocked etc. — do not try other tokens
            raise e
        if user_info is not None:
            if source != "cookie":
                _log.debug("Auth via %s for uid=%s", source, user_info.get("id"))
            return user_info
        last_err = "登录已失效，请重新登录"

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=last_err)


async def get_current_user(request: Request) -> dict:
    return await _resolve_user(request)


async def get_current_user_optional(request: Request) -> dict | None:
    try:
        return await _resolve_user(request)
    except HTTPException:
        return None


# 向后兼容：部分路由曾使用不带 response 参数的版本
get_current_user_strict = get_current_user


def require_role(*roles: str):
    """角色检查依赖工厂。用法: Depends(require_role('admin', 'reviewer'))"""
    async def _checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "权限不足")
        return user
    return _checker


require_admin = require_role("admin")


def public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "authorName": row.get("author_name") or "",
        "avatarUrl": row.get("avatar_url") or "",
        "role": row.get("role") or "user",
    }


import json

from .redis_client import get_redis


async def cache_get(key: str):
    redis = get_redis()
    raw = await redis.get(key)
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


async def cache_set(key: str, data, ttl: int = 60) -> None:
    redis = get_redis()
    await redis.setex(key, ttl, json.dumps(data, ensure_ascii=False, default=str))


async def cache_del(key: str) -> None:
    redis = get_redis()
    await redis.delete(key)
