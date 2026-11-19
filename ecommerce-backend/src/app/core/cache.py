import json
import structlog
from redis.asyncio import Redis, ConnectionPool
from app.core.config import get_settings

settings = get_settings()
logger = structlog.get_logger("cache")

_pool = ConnectionPool.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> Redis:
    return Redis(connection_pool=_pool)


async def close_redis_pool() -> None:
    try:
        await _pool.disconnect()
    except Exception as exc:  # noqa: BLE001
        logger.warning("redis_pool_close_failed", error=str(exc))


async def cache_get(key: str) -> dict | list | None:
    try:
        redis = get_redis()
        value = await redis.get(key)
        return json.loads(value) if value else None
    except Exception as exc:  # noqa: BLE001 - degrade gracefully if Redis is down
        logger.warning("cache_get_failed", key=key, error=str(exc))
        return None


async def cache_set(key: str, value, ttl: int | None = None) -> None:
    try:
        redis = get_redis()
        await redis.set(key, json.dumps(value), ex=ttl or settings.cache_ttl_seconds)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully if Redis is down
        logger.warning("cache_set_failed", key=key, error=str(exc))


async def cache_delete_pattern(pattern: str) -> None:
    """Invalidate all keys matching a pattern."""
    try:
        redis = get_redis()
        async for key in redis.scan_iter(match=pattern):
            await redis.delete(key)
    except Exception as exc:  # noqa: BLE001 - degrade gracefully if Redis is down
        logger.warning("cache_delete_pattern_failed", pattern=pattern, error=str(exc))
