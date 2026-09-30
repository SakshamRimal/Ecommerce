import json 
from redis.asyncio import Redis , ConnectionPool
from app.core.config import get_settings

settings = get_settings()

_pool = ConnectionPool.from_url(settings.redis_url , decode_responses=True)

def get_redis() -> Redis:
    return Redis(connection_pool=_pool)

async def cache_get(key: str) -> dict | list | None:
    redis = get_redis()
    value = await redis.get(key)
    return json.loads(value) if value else None

async def cache_set(key:str , value , ttl:int | None = None) -> None:
    redis = get_redis()
    await redis.set(key , json.dumps(value) , ex=ttl or settings.cache_ttl_seconds)

async def cache_delete_pattern(pattern: str) -> None:
    """Ivalidate all key matching a pattern """
    redis = get_redis()
    async for key in redis.scan_iter(match=pattern):
        await redis.delete(key)