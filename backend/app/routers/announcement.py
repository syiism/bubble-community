from fastapi import APIRouter, Depends, Response

from app.auth import get_current_user, cache_get, cache_set
from app.modules.database import get_db_context
from app.modules.repositories import AnnouncementRepository

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


@router.get("")
async def get_active_announcements(user=Depends(get_current_user), response: Response = None):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Vary"] = "Cookie"
    cached = await cache_get("cache:announcements:active")
    if cached:
        return cached
    async with get_db_context() as db:
        announcements = await AnnouncementRepository.get_active(db)
    data = {
        "code": 0,
        "announcements": [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "priority": a.priority,
                "createdAt": a.created_at.isoformat() if a.created_at else "",
            }
            for a in announcements
        ],
    }
    await cache_set("cache:announcements:active", data, 60)
    return data


@router.get("/all")
async def get_all_announcements(user=Depends(get_current_user), response: Response = None):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Vary"] = "Cookie"
    async with get_db_context() as db:
        announcements = await AnnouncementRepository.get_all(db)
    return {
        "code": 0,
        "announcements": [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "priority": a.priority,
                "isActive": bool(a.is_active),
                "createdAt": a.created_at.isoformat() if a.created_at else "",
            }
            for a in announcements
        ],
    }
