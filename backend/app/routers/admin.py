from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth import require_admin
from app.modules.database import get_db_context
from app.modules.repositories import (
    UserRepository,
    BubbleRepository,
    UserFavoriteRepository,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class RoleBody(BaseModel):
    role: str


@router.get("/stats")
async def admin_stats(user=Depends(require_admin)):
    async with get_db_context() as db:
        from sqlalchemy import func, select
        from app.modules.user import User
        from app.modules.bubble import Bubble

        total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
        total_bubbles = (await db.execute(select(func.count(Bubble.id)))).scalar() or 0
        official_count = (await db.execute(
            select(func.count(Bubble.id)).filter(Bubble.is_official == True)
        )).scalar() or 0
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

    return {
        "code": 0,
        "stats": {
            "totalUsers": total_users,
            "totalBubbles": total_bubbles,
            "officialBubbles": official_count,
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
    user=Depends(require_admin),
):
    async with get_db_context() as db:
        from sqlalchemy import func, select, or_
        from app.modules.user import User

        filters = []
        if query:
            filters.append(
                or_(User.username.ilike(f"%{query}%"), User.author_name.ilike(f"%{query}%"))
            )

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
    if body.role not in ("user", "admin"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "角色只能是 user 或 admin")

    async with get_db_context() as db:
        target = await UserRepository.get_by_id(db, user_id)
        if not target:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")

        # 防止自己撤销自己的管理员
        if target.id == user["id"] and body.role != "admin":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能撤销自己的管理员权限")

        await UserRepository.update(db, target, role=body.role)

    return {"code": 0, "role": body.role}
