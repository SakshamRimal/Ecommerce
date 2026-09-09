from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.rate_limiter import limiter
from app.core.exceptions import AppException
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.job_queue import close_job_queue
from app.middlewares.request_context import RequestContextMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware
from app.db.session import engine 
from app.api.v1.router import api_router
from app.core.elasticsearch import close_es_client
from app.core.elasticsearch import get_es_client
from app.core.search_index import ensure_product_index_exists

configure_logging()
logger = get_logger("startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Startup tasks
    
    logger.info("app_starting", env=get_settings().app_env)
    await ensure_product_index_exists(get_es_client())  # Ensure the product index exists in Elasticsearch
    yield
    
    #shutdown tasks
    logger.info("app_stopping", env=get_settings().app_env)
    await engine.dispose()  # Close the database connection pool
    await close_es_client()  # Close the Elasticsearch client connection pool
    await close_job_queue()  # Close the job queue connection pool
    logger.info("db_connection_pool_closed")
    
def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> Response:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
        
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router)

    app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,  # NEVER use "*" in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    )
    
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    
    return app

app = create_app()
    