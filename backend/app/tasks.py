"""Background tasks for the application."""
import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from .redis_client import get_redis

_log = logging.getLogger("tasks")

CONFIRM_FLUSH_INTERVAL = 10  # seconds

_ASYNC_DB_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
_FLUSH_LUA = """
local members = redis.call('SMEMBERS', 'pending_confirmations')
redis.call('DEL', 'pending_confirmations')
return members
"""


async def flush_confirmations():
    """Periodically flush pending announcement confirmations from Redis to MySQL."""
    engine = create_async_engine(_ASYNC_DB_URL, pool_size=2, max_overflow=5)
    redis = get_redis()
    lua_hash = None

    try:
        lua_hash = await redis.script_load(_FLUSH_LUA)

        while True:
            await asyncio.sleep(CONFIRM_FLUSH_INTERVAL)
            try:
                raw = await redis.evalsha(lua_hash, 0)
                if not raw:
                    continue

                rows = []
                for item in raw:
                    parts = item.split(":")
                    if len(parts) == 2:
                        rows.append({"user_id": int(parts[0]), "announcement_id": int(parts[1])})

                if not rows:
                    continue

                async with engine.begin() as conn:
                    await conn.execute(
                        text("""
                            INSERT IGNORE INTO announcement_confirmations
                                (user_id, announcement_id, created_at)
                            VALUES (:user_id, :announcement_id, NOW())
                        """),
                        rows,
                    )

                _log.info("Flushed %d announcement confirmations", len(rows))
            except Exception:
                _log.exception("Flush confirmations iteration failed")
    except asyncio.CancelledError:
        _log.info("Flush confirmations task cancelled")
    finally:
        if lua_hash:
            try:
                await redis.script_exists(lua_hash)
            except Exception:
                pass
        await engine.dispose()
