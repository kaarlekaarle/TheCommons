"""Logging configuration for The Commons."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: The name of the logger, typically __name__ of the module.
        
    Returns:
        A configured structlog logger instance.
    """
    return structlog.get_logger(name)

def setup_file_handler(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> Optional[RotatingFileHandler]:
    """Set up a rotating file handler for logs.
    
    Args:
        log_file: Path to the log file.
        max_bytes: Maximum size of each log file before rotation.
        backup_count: Number of backup files to keep.
        
    Returns:
        A configured RotatingFileHandler or None if log_file is not set.
    """
    if not log_file:
        return None
        
    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler

def configure_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    console_output: bool = True,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: The logging level to use.
        json_format: Whether to use JSON formatting for logs.
        console_output: Whether to output logs to console.
        log_file: Path to the log file for file output.
        max_bytes: Maximum size of each log file before rotation.
        backup_count: Number of backup files to keep.
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Configure standard library logging
    handlers = []
    
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(console_handler)
    
    if log_file:
        file_handler = setup_file_handler(log_file, max_bytes, backup_count)
        if file_handler:
            handlers.append(file_handler)
    
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
    )

    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def add_context(**kwargs: Any) -> None:
    """Add context to all subsequent log entries.
    
    Args:
        **kwargs: Key-value pairs to add to the logging context.
    """
    structlog.contextvars.clear_contextvars()
    for key, value in kwargs.items():
        structlog.contextvars.bind_contextvars(**{key: value}) 