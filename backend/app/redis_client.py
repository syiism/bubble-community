import logging

import redis.asyncio as aioredis

from .config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

_log = logging.getLogger("redis")

_redis: aioredis.Redis | None = None


async def init_redis() -> None:
    global _redis
    _redis = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD or None,
        db=REDIS_DB,
        decode_responses=True,
    )
    await _redis.ping()
    _log.info("Redis connected to %s:%s", REDIS_HOST, REDIS_PORT)


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        _log.info("Redis disconnected")


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized — call init_redis() on startup")
    return _redis
