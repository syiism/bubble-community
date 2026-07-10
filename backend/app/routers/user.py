from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import get_current_user
from ..modules.database import get_db_context
from ..modules.repositories import UserRepository

router = APIRouter(prefix="/api/user", tags=["user"])


class AuthorNameBody(BaseModel):
    name: str = ""


@router.post("/author-name")
def set_author_name(body: AuthorNameBody, user=Depends(get_current_user)):
    user_id = user["id"]
    name = body.name.strip()
    if len(name) > 16:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "署名最多 16 个字符")

    with get_db_context() as db:
        if name:
            existing = UserRepository.get_by_author_name(db, name)
            if existing and existing.id != user_id:
                raise HTTPException(status.HTTP_409_CONFLICT, "该署名已被他人使用")
        UserRepository.update_author_name(db, user_id, name or None)
    return {"code": 0, "authorName": name}
