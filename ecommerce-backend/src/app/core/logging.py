import logging 
import sys 
import structlog

from app.core.config import get_settings

def configure_logging() -> None:
    settings = get_settings()
    
    
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.debug:
        renderer = structlog.dev.ConsoleRenderer() # human readable output for development
        
    else:
        renderer = structlog.processors.JSONRenderer() # JSON output for production
        
    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = "app"):
    return structlog.get_logger(name)