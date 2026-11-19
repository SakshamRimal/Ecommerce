"""Refresh/access token revocation.

Redis is the preferred store so revocation works across workers. If Redis is
unreachable the module falls back to a process-local dict: still safe for a
single process, but not shared between replicas.
"""

import time

import structlog

from app.core.cache import get_redis

logger = structlog.get_logger("token_store")

_PREFIX = "auth:revoked:"
_memory_revoked: dict[str, float] = {}
_DEFAULT_TTL_SECONDS = 7 * 24 * 60 * 60


def _ttl_seconds(expires_at) -> int:
    if expires_at is None:
        return _DEFAULT_TTL_SECONDS
    if hasattr(expires_at, "timestamp"):
        expires_at = expires_at.timestamp()
    try:
        remaining = int(float(expires_at) - time.time())
    except (TypeError, ValueError):
        return _DEFAULT_TTL_SECONDS
    return max(remaining, 1)


async def revoke_token(jti: str | None, expires_at=None) -> None:
    if not jti:
        return

    ttl = _ttl_seconds(expires_at)

    try:
        redis = get_redis()
        await redis.set(f"{_PREFIX}{jti}", "1", ex=ttl)
        return
    except Exception as exc:  # noqa: BLE001 - fall back to memory
        logger.warning("token_revocation_redis_unavailable", error=str(exc))

    _memory_revoked[jti] = time.time() + ttl


async def is_token_revoked(jti: str | None) -> bool:
    if not jti:
        return False

    try:
        redis = get_redis()
        if await redis.exists(f"{_PREFIX}{jti}"):
            return True
    except Exception:  # noqa: BLE001 - Redis down: consult memory fallback
        pass

    expires_at = _memory_revoked.get(jti)
    if expires_at is None:
        return False
    if expires_at <= time.time():
        _memory_revoked.pop(jti, None)
        return False
    return True


async def consume_token_once(jti: str | None, expires_at=None) -> bool:
    """Atomically mark a refresh token JTI as consumed.

    Returns True if the token was unused and is now revoked, or False if it
    was already revoked/consumed by an earlier or concurrent request.
    """
    if not jti:
        return True

    ttl = _ttl_seconds(expires_at)

    try:
        redis = get_redis()
        acquired = await redis.set(f"{_PREFIX}{jti}", "1", ex=ttl, nx=True)
        return bool(acquired)
    except Exception as exc:  # noqa: BLE001 - fall back to memory
        logger.warning("token_consume_redis_unavailable", error=str(exc))

    now = time.time()
    existing_exp = _memory_revoked.get(jti)
    if existing_exp is not None and existing_exp > now:
        return False
    _memory_revoked[jti] = now + ttl
    return True


def clear_memory_revocations() -> None:
    """Test helper — drop the in-memory revocation set."""
    _memory_revoked.clear()
