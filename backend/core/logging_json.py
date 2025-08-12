"""Enhanced JSON logging configuration for The Commons."""
import contextvars
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

# Context variables for request tracking
request_id_var = contextvars.ContextVar('request_id', default=None)
user_id_var = contextvars.ContextVar('user_id', default=None)

def get_request_context() -> Dict[str, Any]:
    """Get current request context from context variables."""
    context = {}
    
    request_id = request_id_var.get()
    if request_id:
        context['request_id'] = request_id
    
    user_id = user_id_var.get()
    if user_id:
        context['user_id'] = user_id
    
    return context

def set_request_context(request_id: Optional[str] = None, user_id: Optional[str] = None):
    """Set request context variables."""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)

def clear_request_context():
    """Clear request context variables."""
    request_id_var.set(None)
    user_id_var.set(None)

def add_request_context(processor: Processor) -> Processor:
    """Add request context to log entries."""
    def wrapper(logger, method_name, event_dict):
        # Add request context
        context = get_request_context()
        event_dict.update(context)
        
        # Add timestamp in ISO format
        event_dict['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service name
        event_dict['service'] = 'the-commons-api'
        
        return processor(logger, method_name, event_dict)
    return wrapper

def configure_json_logging(
    log_level: str = "INFO",
    environment: str = "dev",
    service_name: str = "the-commons-api"
) -> None:
    """Configure structured JSON logging.
    
    Args:
        log_level: The logging level to use.
        environment: The environment (dev, staging, prod).
        service_name: The service name for log identification.
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Configure standard library logging
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        stream=sys.stdout,
    )

    # Configure structlog with JSON formatting
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_request_context(structlog.processors.JSONRenderer()),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_json_logger(name: str) -> structlog.BoundLogger:
    """Get a structured JSON logger instance.
    
    Args:
        name: The name of the logger, typically __name__ of the module.
        
    Returns:
        A configured structlog logger instance with JSON formatting.
    """
    return structlog.get_logger(name)

def log_request_start(
    logger: structlog.BoundLogger,
    request_id: str,
    method: str,
    path: str,
    user_id: Optional[str] = None,
    **kwargs
):
    """Log the start of a request with structured context."""
    context = {
        'request_id': request_id,
        'method': method,
        'path': path,
        'event_type': 'request_start',
    }
    if user_id:
        context['user_id'] = user_id
    context.update(kwargs)
    
    logger.info("Request started", **context)

def log_request_end(
    logger: structlog.BoundLogger,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    user_id: Optional[str] = None,
    **kwargs
):
    """Log the end of a request with structured context."""
    context = {
        'request_id': request_id,
        'method': method,
        'path': path,
        'status_code': status_code,
        'response_time_ms': round(response_time * 1000, 2),
        'event_type': 'request_end',
    }
    if user_id:
        context['user_id'] = user_id
    context.update(kwargs)
    
    logger.info("Request completed", **context)

def log_error(
    logger: structlog.BoundLogger,
    error: Exception,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
):
    """Log an error with structured context."""
    context = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'event_type': 'error',
    }
    if request_id:
        context['request_id'] = request_id
    if user_id:
        context['user_id'] = user_id
    context.update(kwargs)
    
    logger.error("Error occurred", **context, exc_info=True)
