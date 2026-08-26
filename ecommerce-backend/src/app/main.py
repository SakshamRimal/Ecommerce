from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.middlewares.request_context import RequestContextMiddleware
from app.db.session import engine 
from app.api.v1.router import api_router

configure_logging()
logger = get_logger("startup")

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # Startup tasks
    
    logger.info("app_starting", env=get_settings().app_env)
    yield
    
    #shutdown tasks
    logger.info("app_stopping", env=get_settings().app_env)
    await engine.dispose()  # Close the database connection pool
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
    
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router)
    return app

app = create_app()
    