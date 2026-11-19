from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

_settings = get_settings()

# Memory storage is per process: with multiple workers the effective limit is
# multiplied. Set RATE_LIMIT_STORAGE_URI to a Redis URL in production.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_settings.rate_limit_storage_uri or "memory://",
)
