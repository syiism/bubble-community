import secrets

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, Response
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from sqlalchemy import func, select, or_

from app.svg_util import fill_svg
from app.auth import get_current_user, get_current_user_strict, cache_get, cache_set, cache_del
from app.modules.bubble import Bubble
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
    category: str = "original"


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


def _row_to_style(row, user_id, imported_set, favorite_set, users_map=None):
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
        "category": row.category or "original",
        "mine": mine,
        "imported": row.id in imported_set,
        "favorited": row.id in favorite_set,
        "uses": 0,
        "author": row.author_name or ("" if row.is_official else "匿名书友"),
        "creatorUsername": (users_map or {}).get(row.user_id, ""),
        "shareCode": row.share_code if mine else "",
    }


def _section_filters(section: str, user_id: int, category: str, q: str):
    """Build SQLAlchemy filters for a list section."""
    from app.modules.imported_bubble import ImportedBubble
    from app.modules.user_favorite import UserFavorite

    filters = []
    if category:
        filters.append(Bubble.category == category)
    if q:
        like = f"%{q}%"
        filters.append(or_(Bubble.name.ilike(like), Bubble.author_name.ilike(like)))

    if section == "public":
        filters.append(or_(Bubble.is_public == True, Bubble.is_official == True))
    elif section == "mine":
        filters.append(Bubble.user_id == user_id)
    elif section == "favorites":
        filters.append(
            Bubble.id.in_(select(UserFavorite.bubble_id).where(UserFavorite.user_id == user_id))
        )
    elif section == "imported":
        filters.append(
            Bubble.id.in_(select(ImportedBubble.bubble_id).where(ImportedBubble.user_id == user_id))
        )
    else:
        filters.append(or_(Bubble.is_public == True, Bubble.is_official == True))
    return filters


async def _section_counts(db, user_id: int) -> dict:
    async def _count_plain(section: str) -> int:
        filters = _section_filters(section, user_id, "", "")
        return (await db.execute(select(func.count(Bubble.id)).where(*filters))).scalar() or 0

    mine = await _count_plain("mine")
    favorites = await _count_plain("favorites")
    imported = await _count_plain("imported")
    public = await _count_plain("public")

    my_public = (await db.execute(
        select(func.count(Bubble.id)).where(Bubble.user_id == user_id, Bubble.is_public == True)
    )).scalar() or 0
    my_private = (await db.execute(
        select(func.count(Bubble.id)).where(Bubble.user_id == user_id, Bubble.is_public == False)
    )).scalar() or 0

    from app.modules.user_current_bubble import UserCurrentBubble
    total_uses = (await db.execute(
        select(func.count(UserCurrentBubble.user_id)).where(
            UserCurrentBubble.bubble_id.in_(select(Bubble.id).where(Bubble.user_id == user_id))
        )
    )).scalar() or 0

    return {
        "mine": mine,
        "favorites": favorites,
        "imported": imported,
        "public": public,
        "myPublic": my_public,
        "myPrivate": my_private,
        "totalUses": total_uses,
    }


@router.get("")
async def list_bubbles(
    user=Depends(get_current_user),
    response: Response = None,
    section: str = Query("public", max_length=16),
    page: int = Query(1, ge=1),
    size: int = Query(18, ge=1, le=50),
    sort: str = Query("new", max_length=8),
    q: str = Query("", max_length=64),
    category: str = Query("", max_length=32),
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Vary"] = "Cookie"

    if section not in ("public", "mine", "favorites", "imported"):
        section = "public"
    if sort not in ("new", "hot"):
        sort = "new"

    user_id = user["id"]
    q = (q or "").strip()

    async with get_db_context() as db:
        from app.modules.user import User
        from app.modules.user_current_bubble import UserCurrentBubble

        current_bubble = await UserCurrentBubbleRepository.get_by_user_id(db, user_id)
        current_bubble_id = current_bubble.bubble_id if current_bubble else 0

        filters = _section_filters(section, user_id, category, q)

        total = (await db.execute(
            select(func.count(Bubble.id)).where(*filters)
        )).scalar() or 0

        uses_subq = (
            select(
                UserCurrentBubble.bubble_id.label("bid"),
                func.count(UserCurrentBubble.user_id).label("use_count"),
            )
            .group_by(UserCurrentBubble.bubble_id)
            .subquery()
        )

        stmt = select(Bubble).where(*filters)
        if sort == "hot":
            stmt = (
                stmt.outerjoin(uses_subq, Bubble.id == uses_subq.c.bid)
                .order_by(
                    Bubble.is_official.desc(),
                    func.coalesce(uses_subq.c.use_count, 0).desc(),
                    Bubble.id.desc(),
                )
            )
        else:
            stmt = stmt.order_by(Bubble.is_official.desc(), Bubble.id.desc())

        stmt = stmt.offset((page - 1) * size).limit(size)
        rows = list((await db.execute(stmt)).scalars().all())

        imported_set = await ImportedBubbleRepository.get_imported_ids(db, user_id)
        favorite_set = await UserFavoriteRepository.get_favorite_ids(db, user_id)
        user_info = await UserRepository.get_by_id(db, user_id)

        bubble_ids = [b.id for b in rows]
        uses_map = await BubbleRepository.get_bubble_uses_batch(db, bubble_ids)

        user_ids = {b.user_id for b in rows if b.user_id}
        users_map = {}
        if user_ids:
            users_result = await db.execute(select(User).filter(User.id.in_(user_ids)))
            for u in users_result.scalars().all():
                users_map[u.id] = u.username

        items = []
        for b in rows:
            style = _row_to_style(b, user_id, imported_set, favorite_set, users_map)
            style["uses"] = uses_map.get(b.id, 0)
            items.append(style)

        current_id = current_bubble_id or 0
        current_bubble_style = None
        if current_id:
            if current_id not in {b.id for b in rows}:
                cb = await BubbleRepository.get_by_id(db, current_id)
                if cb:
                    current_bubble_style = _row_to_style(
                        cb, user_id, imported_set, favorite_set, users_map
                    )
                    current_bubble_style["uses"] = (
                        await BubbleRepository.get_bubble_uses(db, current_id)
                    )
                    # fill creator username
                    if cb.user_id and cb.user_id not in users_map:
                        cu = await UserRepository.get_by_id(db, cb.user_id)
                        if cu:
                            current_bubble_style["creatorUsername"] = cu.username
            else:
                current_bubble_style = next(
                    (s for s in items if s["id"] == current_id), None
                )

        counts = await _section_counts(db, user_id)
        has_more = page * size < total

        return {
            "code": 0,
            "allowed": True,
            "canUpload": True,
            "authorName": (user_info.author_name if user_info else "") or "",
            "style": current_id,
            "currentBubble": current_bubble_style,
            "favoritesCount": counts["favorites"],
            "section": section,
            "page": page,
            "size": size,
            "total": total,
            "hasMore": has_more,
            "counts": counts,
            "items": items,
            # backward compat for Profile until migrated
            "styles": items,
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
            "Vary": "Cookie",
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
            category=body.category or "original",
        )
        style = _row_to_style(bubble, user_id, set(), set())
    await cache_del("cache:community-counts")
    await cache_del("cache:bubbles:public-list")
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
            category=body.category or "original",
        )
        # 重新读取以获得更新后的数据（含 updated_at）
        updated = await BubbleRepository.get_by_id(db, bubble_id)
        imported_set = await ImportedBubbleRepository.get_imported_ids(db, user_id)
        favorite_set = await UserFavoriteRepository.get_favorite_ids(db, user_id)
        style = _row_to_style(updated, user_id, imported_set, favorite_set)
    await cache_del("cache:community-counts")
    await cache_del("cache:bubbles:public-list")
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
    await cache_del("cache:community-counts")
    await cache_del("cache:bubbles:public-list")
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
    await cache_del("cache:community-counts")
    await cache_del("cache:bubbles:public-list")
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


@router.get("/community-counts")
async def community_counts():
    cached = await cache_get("cache:community-counts")
    if cached:
        return cached
    async with get_db_context() as db:
        total_public = (
            await db.execute(
                select(func.count(Bubble.id)).where(Bubble.is_public == True)
            )
        ).scalar() or 0
        total_private = (
            await db.execute(
                select(func.count(Bubble.id)).where(Bubble.is_public == False)
            )
        ).scalar() or 0
    data = {
        "code": 0,
        "totalPublic": total_public,
        "totalPrivate": total_private,
    }
    await cache_set("cache:community-counts", data, 60)
    return data