"""Central logging configuration."""
from __future__ import annotations

import json
import logging
import logging.config
from pathlib import Path

from config.settings import get_settings


def configure_logging() -> None:
    settings = get_settings()
    log_dir: Path = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
            }
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_file),
                "encoding": "utf-8",
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["file"],
        },
    }
    logging.config.dictConfig(logging_config)


class JsonFormatter(logging.Formatter):
    """Serialize log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)
