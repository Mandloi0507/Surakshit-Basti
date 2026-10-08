import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# Pattern to redact common sensitive values from logs
SECRET_PATTERNS = [
    re.compile(r'(password|token|secret|key|authorization|bearer)[=\s:]+([^\s,;]+)', re.IGNORECASE),
    re.compile(r'postgresql\+psycopg2://[^:]+:([^@]+)@', re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    """Redacts potential secrets, passwords, and tokens from log messages."""
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r'\1=****', redacted)
    return redacted


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON log formatter with contextual fields:
    - timestamp (UTC ISO-8601)
    - level
    - logger
    - message (with secrets redacted)
    - optional context: district_id, scenario_id, data_origin, request_id
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_secrets(record.getMessage()),
        }

        # Include custom context attributes if present
        for attr in ("district_id", "scenario_id", "data_origin", "dataset", "request_id", "duration_ms"):
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        if record.exc_info:
            log_data["exception"] = redact_secrets(self.formatException(record.exc_info))

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures root application logging with structured JSON formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Avoid adding duplicate handlers if called multiple times
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger instance."""
    return logging.getLogger(name)
