import secrets

from fastapi import APIRouter, Body, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.svg_util import fill_svg
from app.auth import get_current_user, get_current_user_strict
from app.modules.database import get_db_context
from app.modules.repositories import (
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
async def list_bubbles(user=Depends(get_current_user), response: Response = None):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    user_id = user["id"]
    async with get_db_context() as db:
        current_bubble = await UserCurrentBubbleRepository.get_by_user_id(db, user_id)
        current_bubble_id = current_bubble.bubble_id if current_bubble else 0

        bubbles = await BubbleRepository.get_visible_bubbles(db, user_id)
        imported_set = await ImportedBubbleRepository.get_imported_ids(db, user_id)
        favorite_set = await UserFavoriteRepository.get_favorite_ids(db, user_id)
        user_info = await UserRepository.get_by_id(db, user_id)

        bubble_ids = [b.id for b in bubbles]
        uses_map = await BubbleRepository.get_bubble_uses_batch(db, bubble_ids)

        styles = []
        for b in bubbles:
            style = _row_to_style(b, user_id, imported_set, favorite_set)
            style["uses"] = uses_map.get(b.id, 0)
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


@router.get("/get-bubble")
async def get_bubble(user=Depends(get_current_user_strict)):
    user_id = user["id"]

    async with get_db_context() as db:
        current_bubble = await UserCurrentBubbleRepository.get_by_user_id(db, user_id)
        if current_bubble:
            bubble_id = current_bubble.bubble_id
        else:
            fallback = await BubbleRepository.get_official_first(db)
            if not fallback:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "未设置气泡")
            bubble_id = fallback.id

        bubble = await BubbleRepository.get_by_id(db, bubble_id)

    if not bubble:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")

    svg = fill_svg(bubble.svg_template, color=bubble.color, text_color=bubble.text_color, n=12)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.post("")
async def create_bubble(body: BubbleCreate, user=Depends(get_current_user)):
    if not body.svg.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请填写 SVG")
    user_id = user["id"]
    async with get_db_context() as db:
        user_info = await UserRepository.get_by_id(db, user_id)
        author_name = (user_info.author_name if user_info else "") or ""
        bubble = await BubbleRepository.create(
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
        style = _row_to_style(bubble, user_id, set(), set())
    return {"code": 0, "id": bubble.id, "style": style}


@router.put("/{bubble_id}")
async def update_bubble(bubble_id: int, body: BubbleCreate, user=Depends(get_current_user)):
    user_id = user["id"]
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, bubble_id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能编辑自己的气泡")
        await BubbleRepository.update(
            db,
            bubble,
            name=body.name.strip()[:64] or "未命名",
            description=body.desc.strip()[:120],
            svg_template=body.svg,
            color=body.color,
            text_color=body.textColor,
            is_public=body.public,
        )
        # 重新读取以获得更新后的数据（含 updated_at）
        updated = await BubbleRepository.get_by_id(db, bubble_id)
        imported_set = await ImportedBubbleRepository.get_imported_ids(db, user_id)
        favorite_set = await UserFavoriteRepository.get_favorite_ids(db, user_id)
        style = _row_to_style(updated, user_id, imported_set, favorite_set)
    return {"code": 0, "style": style}


@router.delete("/{bubble_id}")
async def delete_bubble(bubble_id: int, user=Depends(get_current_user)):
    user_id = user["id"]
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, bubble_id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能删除自己的气泡")
        await BubbleRepository.delete(db, bubble_id)
    return {"code": 0}


@router.post("/visibility")
async def set_visibility(body: VisibilityBody, user=Depends(get_current_user)):
    user_id = user["id"]
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, body.id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能修改自己的气泡")
        await BubbleRepository.update(db, bubble, is_public=body.public)
        # 构造 style 对象返回，imported/favorited 由前端从本地状态继承
        style = _row_to_style(bubble, user_id, set(), set())
        style["public"] = body.public
    return {"code": 0, "style": style}


@router.post("/share")
async def gen_share(body: ShareBody, user=Depends(get_current_user)):
    user_id = user["id"]
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, body.id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        if bubble.user_id != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "只能分享自己的气泡")
        code = bubble.share_code
        if not code:
            for attempt in range(8):
                code = "B" + secrets.token_hex(4).upper()
                existing = await BubbleRepository.get_by_share_code(db, code)
                if not existing:
                    try:
                        await BubbleRepository.update(db, bubble, share_code=code)
                        break
                    except IntegrityError:
                        await db.rollback()
                        if attempt == 7:
                            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "生成分享码失败，请重试")
                        continue
    return {"code": 0, "shareCode": code, "id": body.id}


@router.post("/redeem")
async def redeem(body: RedeemBody, user=Depends(get_current_user)):
    code = body.code.strip().upper()
    if not code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请输入分享码")
    user_id = user["id"]
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_share_code(db, code)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "分享码无效")
        if bubble.user_id == user_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "这是你自己的气泡")
        await ImportedBubbleRepository.import_bubble(db, user_id, bubble.id)
        await db.refresh(bubble)
        imported_set = await ImportedBubbleRepository.get_imported_ids(db, user_id)
        favorite_set = await UserFavoriteRepository.get_favorite_ids(db, user_id)
        style = _row_to_style(bubble, user_id, imported_set, favorite_set)
    return {"code": 0, "id": bubble.id, "name": bubble.name, "style": style}


@router.post("/remove-imported")
async def remove_imported(bubble_id: int = Body(..., embed=True), user=Depends(get_current_user)):
    user_id = user["id"]
    async with get_db_context() as db:
        await ImportedBubbleRepository.remove_imported(db, user_id, bubble_id)
    return {"code": 0}


@router.post("/current")
async def set_current(style: int | str = Body(..., embed=True), user=Depends(get_current_user)):
    user_id = user["id"]
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, int(style))
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        # 记录切换前的气泡，用于更新两边的 uses 计数
        prev = await UserCurrentBubbleRepository.get_by_user_id(db, user_id)
        prev_id = prev.bubble_id if prev else None
        await UserCurrentBubbleRepository.set_current(db, user_id, int(style))
        # 返回新旧气泡的 uses 计数，前端可精准更新本地状态
        new_uses = await BubbleRepository.get_bubble_uses(db, int(style))
        result = {"code": 0, "uses": new_uses}
        if prev_id and prev_id != int(style):
            prev_uses = await BubbleRepository.get_bubble_uses(db, prev_id)
            result["prevId"] = prev_id
            result["prevUses"] = prev_uses
    return result


@router.post("/favorite")
async def set_favorite(body: FavoriteBody, user=Depends(get_current_user)):
    user_id = user["id"]
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, body.id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        await UserFavoriteRepository.set_favorite(db, user_id, body.id, body.favorite)
        fav_count = await UserFavoriteRepository.count_favorites(db, user_id)
    return {"code": 0, "favorited": body.favorite, "favoritesCount": fav_count}