import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings

_STANDARD_RECORD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys())


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in vars(record).items():
            if key not in _STANDARD_RECORD_ATTRS:
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging():
    settings = get_settings()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.LOG_LEVEL)
