from fastapi import APIRouter, Depends, Response

from app.auth import get_current_user, get_current_user_optional, cache_get, cache_set, cache_del
from app.modules.database import get_db_context
from app.modules.repositories import AnnouncementRepository, AnnouncementConfirmationRepository
from app.redis_client import get_redis

router = APIRouter(prefix="/api/announcements", tags=["announcements"])

CONFIRMED_CACHE_TTL = 60


@router.get("")
async def get_active_announcements(user=Depends(get_current_user_optional), response: Response = None):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Vary"] = "Cookie"
    cached = await cache_get("cache:announcements:active")
    if cached:
        data = cached
    else:
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

    # 已登录用户：过滤掉已确认的公告
    if user:
        user_id = user["id"]
        confirmed = await _get_user_confirmed_ids(user_id)
        if confirmed:
            data["announcements"] = [a for a in data["announcements"] if a["id"] not in confirmed]

    return data


async def _get_user_confirmed_ids(user_id: int) -> set[int]:
    redis = get_redis()
    key = f"cache:user:{user_id}:confirmed_anns"
    raw = await redis.smembers(key)
    if raw:
        return {int(x) for x in raw}
    async with get_db_context() as db:
        ids = await AnnouncementConfirmationRepository.get_confirmed_ids(db, user_id)
    if ids:
        await redis.sadd(key, *ids)
        await redis.expire(key, CONFIRMED_CACHE_TTL)
    return ids


@router.post("/confirm")
async def confirm_announcements(body: dict, user=Depends(get_current_user), response: Response = None):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Vary"] = "Cookie"
    announcement_ids = body.get("announcement_ids", [])
    if not announcement_ids:
        return {"code": 0}
    user_id = user["id"]
    redis = get_redis()
    pipe = redis.pipeline()
    for ann_id in announcement_ids:
        pipe.sadd("pending_confirmations", f"{user_id}:{ann_id}")
        pipe.sadd(f"cache:user:{user_id}:confirmed_anns", ann_id)
    pipe.expire(f"cache:user:{user_id}:confirmed_anns", CONFIRMED_CACHE_TTL)
    await pipe.execute()
    return {"code": 0}


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
