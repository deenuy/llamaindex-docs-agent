import logging
import os
from datetime import datetime
from logging.config import dictConfig
from typing import Optional, Dict, Any
from contextvars import ContextVar

from app.utils.config.config_loader import ConfigLoader

DEFAULT_LOGGER_NAME = "project_logger"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENV = os.getenv("ENVIRONMENT", "prod").lower()

# ✅ Request ID context variable (for per-request logging)
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="N/A")

def get_request_id() -> str:
    """Get the current request ID from context, or 'N/A' if not set."""
    return request_id_ctx_var.get() or "N/A"

class RequestIdFilter(logging.Filter):
    """Logging filter to inject request_id into log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True

def setup_logger(
        env: str = DEFAULT_ENV,
        custom_formatters: Optional[Dict[str, Dict[str, Any]]] = None,
        custom_filters: Optional[Dict[str, Dict[str, Any]]] = None,
) -> logging.Logger:
    """
    Sets up a centralized structured logger with console and rotating file output.

    Args:
        env (str): Environment string (prod, dev, etc.).
        custom_formatters (dict, optional): Custom formatters if needed.
        custom_filters (dict, optional): Custom filters if needed.

    Returns:
        logging.Logger: Configured centralized logger instance.
    """
    existing_logger = logging.getLogger(DEFAULT_LOGGER_NAME)
    if existing_logger.handlers:
        existing_logger.debug("Logger already initialized, skipping reconfiguration.")
        return existing_logger  # ✅ Prevents multiple handler registrations

    try:
        # ✅ Load external config
        config_loader = ConfigLoader(env)
        config = config_loader.load_config()

        log_config = config.get("logs", {})
        log_dir = log_config.get("dir", "./logs")
        os.makedirs(log_dir, exist_ok=True)

        log_level = log_config.get("level", DEFAULT_LOG_LEVEL).upper()

        # ✅ Timestamped log filename
        file_name = f"{log_config.get('fname', 'py4j.logger')}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        log_filename = os.path.join(log_dir, f"{file_name}.log")

        base_formatter = {
            "class": "logging.Formatter",
            "format": "%(levelname)s %(asctime)s [%(filename)s:%(lineno)d] [RequestID:%(request_id)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }

        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": base_formatter
            },
            "filters": {
                "request_id": {"()": RequestIdFilter}
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["request_id"],
                    "level": log_level,
                },
                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "formatter": "default",
                    "filters": ["request_id"],
                    "filename": log_filename,
                    "when": log_config.get("when", "midnight"),
                    "backupCount": log_config.get("backup_count", 7),
                    "level": log_level,
                },
            },
            "loggers": {
                DEFAULT_LOGGER_NAME: {
                    "handlers": ["console", "file"],
                    "level": log_level,
                    "propagate": False,
                }
            },
        }

        # ✅ Optional custom formatters/filters
        if custom_formatters:
            logging_config["formatters"].update(custom_formatters)
        if custom_filters:
            logging_config["filters"].update(custom_filters)

        # ✅ Apply logging configuration
        dictConfig(logging_config)

        # ✅ Record factory for global ContextVar injection (background tasks safe)
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = get_request_id()  # ✅ Safe fallback
            record.msg = str(record.msg).replace("\n", "<N>")  # Optional cleanup
            return record

        logging.setLogRecordFactory(record_factory)

        return logging.getLogger(DEFAULT_LOGGER_NAME)

    except Exception as e:
        raise RuntimeError(f"Failed to initialize logger: {e}") from e
