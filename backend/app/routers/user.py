import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel

from app.auth import get_current_user, invalidate_user_cache
from app.modules.database import get_db_context
from app.modules.repositories import UserRepository

router = APIRouter(prefix="/api/user", tags=["user"])

AVATAR_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "avatars"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB


class AuthorNameBody(BaseModel):
    name: str = ""


class UsernameBody(BaseModel):
    username: str = ""


def _avatar_url(filename: str, ts: int = 0) -> str:
    url = f"/bubble-community/avatars/{filename}"
    if ts:
        url += f"?t={ts}"
    return url


@router.post("/author-name")
async def set_author_name(body: AuthorNameBody, user=Depends(get_current_user)):
    user_id = user["id"]
    name = body.name.strip()
    if len(name) > 16:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "署名最多 16 个字符")

    async with get_db_context() as db:
        if name:
            existing = await UserRepository.get_by_author_name(db, name)
            if existing and existing.id != user_id:
                raise HTTPException(status.HTTP_409_CONFLICT, "该署名已被他人使用")
        await UserRepository.update_author_name(db, user_id, name or None)
    await invalidate_user_cache(user_id)
    return {"code": 0, "authorName": name}


@router.post("/username")
async def set_username(body: UsernameBody, user=Depends(get_current_user)):
    user_id = user["id"]
    new_username = body.username.strip()
    if not new_username:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户名不能为空")

    async with get_db_context() as db:
        existing = await UserRepository.get_by_username(db, new_username)
        if existing and existing.id != user_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "该用户名已被他人使用")
        target = await UserRepository.get_by_id(db, user_id)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")

        # 每 30 天可修改一次
        if target.username_updated_at:
            days_since = (datetime.now(timezone.utc).replace(tzinfo=None) - target.username_updated_at).days
            if days_since < 30:
                remaining = 30 - days_since
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"用户名每30天可修改一次，请{remaining}天后再试",
                )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await UserRepository.update(db, target, username=new_username, username_updated_at=now)
    await invalidate_user_cache(user_id)
    return {"code": 0, "username": new_username}


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user=Depends(get_current_user)):
    user_id = user["id"]

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "仅支持 JPG/PNG/GIF/WebP 格式")

    # 读取文件内容校验大小
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "文件大小不能超过 2MB")

    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}[file.content_type]
    filename = f"user_{user_id}{ext}"

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    (AVATAR_DIR / filename).write_bytes(data)

    import time
    avatar_url = _avatar_url(filename, int(time.time()))

    async with get_db_context() as db:
        target = await UserRepository.get_by_id(db, user_id)
        if target:
            await UserRepository.update(db, target, avatar_url=avatar_url)
    await invalidate_user_cache(user_id)
    return {"code": 0, "avatarUrl": avatar_url}
