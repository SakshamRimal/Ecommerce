from arq import create_pool
from arq.connections import RedisSettings , ArqRedis
from app.core.config import get_settings

settings = get_settings()
_pool: ArqRedis | None = None

async def get_job_queue() -> ArqRedis:
    global _pool 
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(settings.arq_redis_url))
    return _pool

async def close_job_queue() -> None:
    global _pool 
    if _pool is not None:
        await _pool.close()
        _pool = None