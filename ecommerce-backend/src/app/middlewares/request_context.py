"""
Every request needs a unique ID so you can trace it through logs, even across services.
"""

import uuid 
import time 
import structlog 
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self , request: Request, call_next):
        
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        start = time.perf_counter()
        response = await call_next(request)
        duration = round((time.perf_counter() - start))
        response.headers["X-Request-ID"] = request_id
        
        logger = structlog.get_logger("http")
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration=duration,
        )
        return response

