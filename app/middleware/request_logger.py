"""Request logging middleware with structured JSON output.

Registers before_request and after_request hooks that capture request
metadata and emit structured JSON log entries for every API request.

Validates: Requirements 25.1, 25.2
- 25.1: Logs method, path, user identifier, status code, and duration_ms.
- 25.2: Uses structured JSON logging format.
"""

import logging
import json
import time
from datetime import datetime, timezone

from flask import g, request


class JSONFormatter(logging.Formatter):
    """Custom log formatter that outputs JSON-structured log records."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach extra structured fields if present
        if hasattr(record, "json_fields"):
            log_data.update(record.json_fields)
        return json.dumps(log_data)


def init_request_logging(app):
    """Register before_request and after_request hooks for structured request logging.

    Args:
        app: The Flask application instance.
    """
    logger = logging.getLogger("request_logger")

    # Only add handler if none exist (avoid duplicate handlers on re-init)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Prevent propagation to root logger to avoid duplicate output
    logger.propagate = False

    @app.before_request
    def _start_timer():
        """Record request start time in g for duration calculation."""
        g._request_start_time = time.perf_counter()

    @app.after_request
    def _log_request(response):
        """Log structured JSON entry after each request completes."""
        duration_ms = None
        if hasattr(g, "_request_start_time"):
            duration_ms = round(
                (time.perf_counter() - g._request_start_time) * 1000, 2
            )

        user_id = getattr(g, "current_user_id", None)

        log_entry = {
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "remote_addr": request.remote_addr,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Emit structured log using extra field
        logger.info(
            f"{request.method} {request.path} {response.status_code}",
            extra={"json_fields": log_entry},
        )

        return response
