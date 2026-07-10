import secrets

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import get_current_user
from ..modules.database import get_db_context
from ..modules.repositories import (
    BubbleRepository,
    UserCurrentBubbleRepository,
    ImportedBubbleRepository,
    UserFavoriteRepository,
    UserRepository,
)

router = APIRouter(prefix="/api/bubbles", tags=["bubbles"])


class BubbleCreate(BaseModel):
    name: str = ""
    desc: str = ""
    svg: str
    color: str = ""
    textColor: str = ""
    public: bool = False


class VisibilityBody(BaseModel):
    id: int
    public: bool


class ShareBody(BaseModel):
    id: int


class RedeemBody(BaseModel):
    code: str


class CurrentBody(BaseModel):
    style: int | str


class FavoriteBody(BaseModel):
    id: int
    favorite: bool


def _row_to_style(row, user_id, imported_set, favorite_set):
    mine = row.user_id == user_id
    return {
        "id": row.id,
        "name": row.name,
        "desc": row.description,
        "svg": row.svg_template,
        "rawSvg": row.svg_template,
        "color": row.color,
        "textColor": row.text_color,
        "official": bool(row.is_official),
        "public": bool(row.is_public),
        "mine": mine,
        "imported": row.id in imported_set,
        "favorited": row.id in favorite_set,
        "uses": 0,
        "author": row.author_name or ("" if row.is_official else "匿名书友"),
        "shareCode": row.share_code if mine else "",
    }


@router.get("")
def list_bubbles(user=Depends(get_current_user)):
    user_id = user["id"]
    with get_db_context() as db:
        current_bubble = UserCurrentBubbleRepository.get_by_user_id(db, user_id)
        current_bubble_id = current_bubble.bubble_id if current_bubble else 0

        bubbles = BubbleRepository.get_visible_bubbles(db, user_id)
        imported_set = ImportedBubbleRepository.get_imported_ids(db, user_id)
        favorite_set = UserFavoriteRepository.get_favorite_ids(db, user_id)
        user_info = UserRepository.get_by_id(db, user_id)

        styles = []
        for b in bubbles:
            style = _row_to_style(b, user_id, imported_set, favorite_set)
            style["uses"] = BubbleRepository.get_bubble_uses(db, b.id)
            styles.append(style)

        current_id = current_bubble_id if current_bubble_id else (styles[0]["id"] if styles else 0)
        visible_ids = {s["id"] for s in styles}
        if current_id not in visible_ids and styles:
            current_id = styles[0]["id"]

        return {
            "code": 0,
            "allowed": True,
            "canUpload": True,
            "authorName": (user_info.author_name if user_info else "") or "",
            "style": current_id,
            "favoritesCount": len(favorite_set),
            "styles": styles,
        }


@router.post("")
def create_bubble(body: BubbleCreate, user=Depends(get_current_user)):
    if not body.svg.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请填写 SVG")
    user_id = user["id"]
    with get_db_context() as db:
        user_info = UserRepository.get_by_id(db, user_id)
        author_name = (user_info.author_name if user_info else "") or ""
        bubble = BubbleRepository.create(
            db,
            user_id=user_id,
            name=body.name.strip()[:64] or "未命名",
            description=body.desc.strip()[:120],
            svg_template=body.svg,
            color=body.color,
            text_color=body.textColor,
            is_public=body.public,
            author_name=author_name,
        )
    return {"code": 0, "id": bubble.id}


@router.put("/{bubble_id}")
def update_bubble(bubble_id: int, body: BubbleCreate, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_db_context() as db:
        bubble = BubbleRepository.get_by_id(db, bubble_id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能编辑自己的气泡")
        BubbleRepository.update(
            db,
            bubble,
            name=body.name.strip()[:64] or "未命名",
            description=body.desc.strip()[:120],
            svg_template=body.svg,
            color=body.color,
            text_color=body.textColor,
            is_public=body.public,
        )
    return {"code": 0}


@router.delete("/{bubble_id}")
def delete_bubble(bubble_id: int, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_db_context() as db:
        bubble = BubbleRepository.get_by_id(db, bubble_id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能删除自己的气泡")
        BubbleRepository.delete(db, bubble_id)
    return {"code": 0}


@router.post("/visibility")
def set_visibility(body: VisibilityBody, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_db_context() as db:
        bubble = BubbleRepository.get_by_id(db, body.id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能修改自己的气泡")
        BubbleRepository.update(db, bubble, is_public=body.public)
    return {"code": 0}


@router.post("/share")
def gen_share(body: ShareBody, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_db_context() as db:
        bubble = BubbleRepository.get_by_id(db, body.id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能分享自己的气泡")
        code = bubble.share_code
        if not code:
            for _ in range(8):
                code = "B" + secrets.token_hex(4).upper()
                existing = BubbleRepository.get_by_share_code(db, code)
                if not existing:
                    break
            BubbleRepository.update(db, bubble, share_code=code)
    return {"code": 0, "shareCode": code}


@router.post("/redeem")
def redeem(body: RedeemBody, user=Depends(get_current_user)):
    code = body.code.strip().upper()
    if not code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请输入分享码")
    user_id = user["id"]
    with get_db_context() as db:
        bubble = BubbleRepository.get_by_share_code(db, code)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "分享码无效")
        if bubble.user_id == user_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "这是你自己的气泡")
        ImportedBubbleRepository.import_bubble(db, user_id, bubble.id)
    return {"code": 0, "id": bubble.id, "name": bubble.name}


@router.post("/current")
def set_current(style: int | str = Body(..., embed=True), user=Depends(get_current_user)):
    user_id = user["id"]
    with get_db_context() as db:
        bubble = BubbleRepository.get_by_id(db, int(style))
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        UserCurrentBubbleRepository.set_current(db, user_id, int(style))
    return {"code": 0}


@router.post("/favorite")
def set_favorite(body: FavoriteBody, user=Depends(get_current_user)):
    user_id = user["id"]
    with get_db_context() as db:
        bubble = BubbleRepository.get_by_id(db, body.id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        UserFavoriteRepository.set_favorite(db, user_id, body.id, body.favorite)
    return {"code": 0}
