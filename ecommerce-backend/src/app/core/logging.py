"""
Strucuted Logging module for the application.
"""
import logging 
import sys 
import structlog
from opentelemetry import trace

from app.core.config import get_settings 

def configure_logging() -> None:
    settings = get_settings()
    
    shared_processors = [
        structlog.contextvars.merge_contextvars,  # pulls request_id etc from context
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.debug:
        renderer = structlog.dev.ConsoleRenderer() # human readable output for development
    else:
        renderer = structlog.processors.JSONRenderer() 
        #machine readable output for production
        
    
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



def add_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        event_dict["trace_id"] = format(span.get_span_context().trace_id, "032x")
    return event_dict
        
"""
Why structlog? It binds context (like request_id) automatically to every log line without you passing it manually everywhere. This is what makes distributed tracing/debugging possible later.

"""
