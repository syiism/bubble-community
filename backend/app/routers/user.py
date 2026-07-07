from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import get_current_user
from ..db import get_conn

router = APIRouter(prefix="/api/user", tags=["user"])


class AuthorNameBody(BaseModel):
    name: str = ""


@router.post("/author-name")
def set_author_name(body: AuthorNameBody, user=Depends(get_current_user)):
    user_id = user["id"]
    name = body.name.strip()
    if len(name) > 16:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "署名最多 16 个字符")

    with get_conn() as conn:
        with conn.cursor() as cur:
            if name:
                cur.execute(
                    "SELECT id FROM users WHERE author_name = %s AND id <> %s",
                    (name, user_id),
                )
                if cur.fetchone():
                    raise HTTPException(status.HTTP_409_CONFLICT, "该署名已被他人使用")
            cur.execute(
                "UPDATE users SET author_name = %s WHERE id = %s",
                (name or None, user_id),
            )
            # 同步到本人创建的气泡，保证公开/分享展示一致
            cur.execute(
                "UPDATE bubbles SET author_name = %s WHERE user_id = %s",
                (name, user_id),
            )
            conn.commit()
    return {"code": 0, "authorName": name}
