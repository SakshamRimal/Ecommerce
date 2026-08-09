from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI 

from app.core.config import get_settings
from app.core.logging import configure_logging , get_logger 
from app.middlewares.request_context import RequestContextMiddleware
from app.db.session import engine
from app.api.v1.router import api_router

configure_logging()
logger = get_logger("startup")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("app_starting" , env=get_settings().app_env)
    yield
    #---shutdown (graceful shutdown) code
    logger.info("app_shutting_down")
    await engine.dispose()
    logger.info("app_shutdown_complete")
    
def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router)
    
    return app

app = create_app()
    