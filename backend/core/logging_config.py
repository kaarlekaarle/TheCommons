import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict, Union

from backend.config import settings


class LogExtra(TypedDict, total=False):
    """Type for extra logging fields."""

    error: str
    status_code: int
    message: str
    log_level: str
    log_format: str
    log_file: str
    exception: Dict[str, str]


class LogRecord(TypedDict, total=False):
    """Type for structured log record."""

    timestamp: str
    level: str
    message: str
    module: str
    function: str
    line: int
    extra: LogExtra


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: LogRecord = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # Add exception info if present
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            if exc_type is not None and exc_value is not None:
                log_data["extra"] = {
                    "exception": {
                        "type": exc_type.__name__,
                        "message": str(exc_value),
                        "traceback": self.formatException(record.exc_info),
                    }
                }

        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO", log_format: str = "json", log_file: str = "app.log"
) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ("json" or "text")
        log_file: Path to log file
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_dir / log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log startup message
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_format": log_format,
            "log_file": str(log_dir / log_file),
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


# Initialize logging with environment-specific settings
if settings.ENV == "production":
    setup_logging(log_level="INFO", log_format="json", log_file="app.log")
else:
    setup_logging(log_level="DEBUG", log_format="text", log_file="app.log")
