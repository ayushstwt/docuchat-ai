import contextvars
from datetime import datetime, timezone
import json
import logging
import sys

from app.core.config import get_settings

# Context variable to hold current request ID across async tasks
request_id_ctx_var = contextvars.ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        return True


class JsonLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_ctx_var.get()),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging() -> None:
    settings = get_settings()

    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if settings.log_format.lower() == "json":
        handler.setFormatter(JsonLogFormatter())
        logging.basicConfig(
            level=level,
            handlers=[handler],
            force=True,
        )
    else:
        log_format = "%(asctime)s | %(levelname)-8s | [%(request_id)s] | %(name)s | %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        handler.setFormatter(logging.Formatter(log_format, date_format))
        logging.basicConfig(
            level=level,
            handlers=[handler],
            force=True,
        )

    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
