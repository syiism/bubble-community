import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel

from app.auth import get_current_user, invalidate_user_cache
from app.modules.database import get_db_context
from app.modules.repositories import UserRepository

router = APIRouter(prefix="/api/user", tags=["user"])

AVATAR_DIR = Path(__file__).resolve().parent.parent / "avatars"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_SIZE = 2 * 1024 * 1024  # 2MB


class AuthorNameBody(BaseModel):
    name: str = ""


def _avatar_url(filename: str) -> str:
    return f"/bubble-community/avatars/{filename}"


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

    avatar_url = _avatar_url(filename)

    async with get_db_context() as db:
        target = await UserRepository.get_by_id(db, user_id)
        if target:
            await UserRepository.update(db, target, avatar_url=avatar_url)
    await invalidate_user_cache(user_id)
    return {"code": 0, "avatarUrl": avatar_url}
