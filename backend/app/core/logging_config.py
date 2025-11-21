import logging
from logging.config import dictConfig
from pathlib import Path
import os


def setup_logging():
    """Configure project-wide logging with daily file rotation."""
    log_dir = Path(os.getenv("AITODAY_LOG_DIR", Path(__file__).resolve().parents[2] / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "backend.log"

    log_level = os.getenv("AITODAY_LOG_LEVEL", "INFO")

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "detailed",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": str(log_file),
                "when": "midnight",
                "backupCount": int(os.getenv("AITODAY_LOG_BACKUP_DAYS", "7")),
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "apscheduler": {"level": "INFO"},
            "uvicorn": {"level": "INFO"},
            "uvicorn.error": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        },
    }

    dictConfig(config)
    logging.getLogger(__name__).info("Logging initialized at %s, writing to %s", log_level, log_file)

