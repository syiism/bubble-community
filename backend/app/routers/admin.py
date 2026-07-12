from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.auth import require_admin, require_role, invalidate_user_cache
from app.modules.database import get_db_context
from app.modules.repositories import (
    UserRepository,
    BubbleRepository,
    UserFavoriteRepository,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class IdListBody(BaseModel):
    ids: list[int]


class RoleBody(BaseModel):
    role: str


class PasswordBody(BaseModel):
    password: str


class BubbleVisibilityBody(BaseModel):
    public: bool


class BubbleEditBody(BaseModel):
    name: str = ""
    desc: str = ""
    svg: str = ""
    color: str = ""
    textColor: str = ""
    public: bool = False
    authorName: str = ""
    userId: int = 0


@router.get("/stats")
async def admin_stats(user=Depends(require_admin), response: Response = None):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    async with get_db_context() as db:
        from sqlalchemy import func, select
        from app.modules.user import User
        from app.modules.bubble import Bubble

        total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
        total_bubbles = (await db.execute(select(func.count(Bubble.id)))).scalar() or 0
        admin_count = (await db.execute(
            select(func.count(User.id)).filter(User.role == "admin")
        )).scalar() or 0
        # 总收藏数
        from app.modules.user_favorite import UserFavorite
        fav_count = (await db.execute(
            select(func.count(UserFavorite.user_id))
        )).scalar() or 0
        # 使用中气泡数（去重）
        from app.modules.user_current_bubble import UserCurrentBubble
        active_bubbles = len(set(
            row[0] for row in (await db.execute(
                select(UserCurrentBubble.bubble_id)
            )).all()
        ))

    # 在线用户数（Redis 中有活跃 session 的用户数）
    online_count = 0
    try:
        from app.redis_client import get_redis
        redis = get_redis()
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match="bubble_tokens:*", count=100)
            online_count += len(keys)
            if cursor == 0:
                break
    except Exception:
        pass

    return {
        "code": 0,
        "stats": {
            "totalUsers": total_users,
            "totalBubbles": total_bubbles,
            "onlineUsers": online_count,
            "adminCount": admin_count,
            "totalFavorites": fav_count,
            "activeBubbles": active_bubbles,
        },
    }


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    query: str = Query("", max_length=64),
    role: str = Query("", max_length=16),
    user=Depends(require_admin),
    response: Response = None,
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    async with get_db_context() as db:
        from sqlalchemy import func, select, or_, and_
        from app.modules.user import User

        filters = []
        if query:
            filters.append(
                or_(User.username.ilike(f"%{query}%"), User.author_name.ilike(f"%{query}%"))
            )
        if role:
            filters.append(User.role == role)

        total = (await db.execute(
            select(func.count(User.id)).where(*filters)
        )).scalar() or 0

        result = await db.execute(
            select(User)
            .where(*filters)
            .order_by(User.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = result.scalars().all()

        # 收集每个用户的统计数据
        user_ids = [u.id for u in rows]
        users_data = []
        for u in rows:
            users_data.append({
                "id": u.id,
                "username": u.username,
                "authorName": u.author_name or "",
                "avatarUrl": u.avatar_url or "",
                "role": u.role or "user",
                "createdAt": u.created_at.isoformat() if u.created_at else "",
            })

    return {
        "code": 0,
        "users": users_data,
        "total": total,
        "page": page,
        "size": size,
    }


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: int, body: RoleBody, user=Depends(require_admin)):
    if body.role not in ("user", "admin", "reviewer"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "角色只能是 user 或 admin")

    async with get_db_context() as db:
        target = await UserRepository.get_by_id(db, user_id)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")

        # 防止自己撤销自己的管理员
        if target.id == user["id"] and body.role != "admin":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能撤销自己的管理员权限")

        await UserRepository.update(db, target, role=body.role)
    await invalidate_user_cache(user_id)
    return {"code": 0, "role": body.role}


@router.put("/users/{user_id}/password")
async def admin_reset_password(user_id: int, body: PasswordBody, user=Depends(require_admin)):
    if len(body.password) < 6:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "密码长度不能少于 6 个字符")

    async with get_db_context() as db:
        target = await UserRepository.get_by_id(db, user_id)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
        await UserRepository.update_password(db, user_id, body.password)
    await invalidate_user_cache(user_id)
    return {"code": 0, "message": "密码已重置"}


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: int, user=Depends(require_admin)):
    async with get_db_context() as db:
        target = await UserRepository.get_by_id(db, user_id)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
        if target.id == user["id"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能删除自己的账号")
        if target.role in ("admin", "reviewer"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能删除管理员或审核员，请先降级")
        await UserRepository.delete_user(db, user_id)
    return {"code": 0}


@router.get("/bubbles")
async def list_bubbles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    query: str = Query("", max_length=64),
    official: str = Query("", max_length=8),
    public: str = Query("", max_length=8),
    start_date: str = Query("", max_length=10),
    end_date: str = Query("", max_length=10),
    user=Depends(require_role("admin", "reviewer")),
    response: Response = None,
):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    async with get_db_context() as db:
        from sqlalchemy import func, select, or_, and_
        from app.modules.bubble import Bubble
        from app.modules.user import User

        filters = []
        if query:
            filters.append(
                or_(
                    Bubble.name.ilike(f"%{query}%"),
                    Bubble.author_name.ilike(f"%{query}%"),
                    Bubble.user_id.in_(
                        select(User.id).filter(User.username.ilike(f"%{query}%"))
                    ),
                )
            )
        if official in ("1", "true"):
            filters.append(Bubble.is_official == True)
        elif official in ("0", "false"):
            filters.append(Bubble.is_official == False)
        if public in ("1", "true"):
            filters.append(Bubble.is_public == True)
        elif public in ("0", "false"):
            filters.append(Bubble.is_public == False)
        if start_date:
            filters.append(Bubble.created_at >= start_date)
        if end_date:
            filters.append(Bubble.created_at <= end_date + " 23:59:59")
        # 审核员只能看到公开气泡
        if user.get("role") == "reviewer":
            filters.append(Bubble.is_public == True)

        total = (await db.execute(
            select(func.count(Bubble.id)).where(*filters)
        )).scalar() or 0

        result = await db.execute(
            select(Bubble)
            .where(*filters)
            .order_by(Bubble.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        rows = result.scalars().all()

        # 查询每个气泡对应的用户名
        user_ids = {r.user_id for r in rows if r.user_id}
        users_map = {}
        if user_ids:
            users_result = await db.execute(
                select(User).filter(User.id.in_(user_ids))
            )
            for u in users_result.scalars().all():
                users_map[u.id] = u.username

        bubbles_data = []
        for b in rows:
            bubbles_data.append({
                "id": b.id,
                "name": b.name,
                "desc": b.description,
                "svg": b.svg_template,
                "rawSvg": b.svg_template,
                "color": b.color or "",
                "textColor": b.text_color or "",
                "official": bool(b.is_official),
                "public": bool(b.is_public),
                "authorName": b.author_name or "",
                "userId": b.user_id,
                "username": users_map.get(b.user_id) or "",
                "createdAt": b.created_at.isoformat() if b.created_at else "",
            })

    return {
        "code": 0,
        "bubbles": bubbles_data,
        "total": total,
        "page": page,
        "size": size,
    }


@router.delete("/bubbles/{bubble_id}")
async def admin_delete_bubble(bubble_id: int, user=Depends(require_admin)):
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, bubble_id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        await BubbleRepository.delete(db, bubble_id)
    return {"code": 0}


@router.post("/users/batch-delete")
async def admin_batch_delete_users(body: IdListBody, user=Depends(require_admin)):
    if not body.ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请选择要删除的用户")
    async with get_db_context() as db:
        for uid in body.ids:
            target = await UserRepository.get_by_id(db, uid)
            if not target:
                continue
            if target.id == user["id"]:
                continue
            if target.role in ("admin", "reviewer"):
                continue
            await UserRepository.delete_user(db, uid)
    return {"code": 0}


@router.post("/bubbles/batch-delete")
async def admin_batch_delete_bubbles(body: IdListBody, user=Depends(require_admin)):
    if not body.ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请选择要删除的气泡")
    async with get_db_context() as db:
        for bid in body.ids:
            bubble = await BubbleRepository.get_by_id(db, bid)
            if not bubble:
                continue
            await BubbleRepository.delete(db, bid)
    return {"code": 0}


@router.put("/bubbles/{bubble_id}/visibility")
async def admin_set_visibility(bubble_id: int, body: BubbleVisibilityBody, user=Depends(require_role("admin", "reviewer"))):
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, bubble_id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        # 审核员不可操作已私有的气泡
        if user.get("role") == "reviewer" and not bubble.is_public:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "审核员不可操作已私有的气泡")
        await BubbleRepository.update(db, bubble, is_public=body.public)
    return {"code": 0, "public": body.public}


@router.put("/bubbles/{bubble_id}")
async def admin_update_bubble(bubble_id: int, body: BubbleEditBody, user=Depends(require_admin)):
    async with get_db_context() as db:
        bubble = await BubbleRepository.get_by_id(db, bubble_id)
        if not bubble:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "气泡不存在")
        kwargs = {
            "name": body.name.strip()[:64] or "未命名",
            "description": body.desc.strip()[:120],
            "svg_template": body.svg,
            "color": body.color,
            "text_color": body.textColor,
            "is_public": body.public,
            "author_name": body.authorName.strip()[:32],
        }
        if body.userId and body.userId != bubble.user_id:
            kwargs["user_id"] = body.userId
        await BubbleRepository.update(db, bubble, **kwargs)
    return {"code": 0}
