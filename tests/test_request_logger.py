"""Tests for request logging middleware.

Validates: Requirements 25.1, 25.2
"""

import json
import logging

import pytest


@pytest.fixture(autouse=True)
def enable_log_propagation():
    """Enable propagation on the request_logger so caplog can capture records."""
    logger = logging.getLogger("request_logger")
    original = logger.propagate
    logger.propagate = True
    yield
    logger.propagate = original


class TestRequestLogger:
    """Tests for the structured request logging middleware."""

    def test_after_request_emits_json_log(self, app, client, caplog):
        """Verify that a request produces a structured JSON log entry (Req 25.2)."""
        logger = logging.getLogger("request_logger")
        with caplog.at_level(logging.INFO, logger="request_logger"):
            response = client.get("/api/v1/health")

        # Find the structured log record
        log_records = [r for r in caplog.records if r.name == "request_logger"]
        assert len(log_records) >= 1

        record = log_records[-1]
        assert hasattr(record, "json_fields")
        fields = record.json_fields

        # Requirement 25.1: method, path, status_code, duration_ms, user_id, remote_addr, timestamp
        assert fields["method"] == "GET"
        assert fields["path"] == "/api/v1/health"
        assert isinstance(fields["status_code"], int)
        assert isinstance(fields["duration_ms"], float)
        assert "user_id" in fields
        assert "remote_addr" in fields
        assert "timestamp" in fields

    def test_log_contains_method_and_path(self, app, client, caplog):
        """Verify method and path are captured (Req 25.1)."""
        with caplog.at_level(logging.INFO, logger="request_logger"):
            client.post("/api/v1/health")

        log_records = [r for r in caplog.records if r.name == "request_logger"]
        assert len(log_records) >= 1
        fields = log_records[-1].json_fields
        assert fields["method"] == "POST"
        assert fields["path"] == "/api/v1/health"

    def test_duration_is_non_negative(self, app, client, caplog):
        """Verify duration_ms is a non-negative number."""
        with caplog.at_level(logging.INFO, logger="request_logger"):
            client.get("/api/v1/health")

        log_records = [r for r in caplog.records if r.name == "request_logger"]
        fields = log_records[-1].json_fields
        assert fields["duration_ms"] >= 0

    def test_user_id_is_none_for_unauthenticated(self, app, client, caplog):
        """Verify user_id is None when no auth is present."""
        with caplog.at_level(logging.INFO, logger="request_logger"):
            client.get("/api/v1/health")

        log_records = [r for r in caplog.records if r.name == "request_logger"]
        fields = log_records[-1].json_fields
        assert fields["user_id"] is None

    def test_json_formatter_produces_valid_json(self, app, client, caplog):
        """Verify the JSONFormatter outputs parseable JSON."""
        from app.middleware.request_logger import JSONFormatter

        formatter = JSONFormatter()
        with caplog.at_level(logging.INFO, logger="request_logger"):
            client.get("/api/v1/health")

        log_records = [r for r in caplog.records if r.name == "request_logger"]
        formatted = formatter.format(log_records[-1])
        parsed = json.loads(formatted)
        assert "timestamp" in parsed
        assert "level" in parsed
        assert parsed["method"] == "GET"

    def test_timestamp_is_iso_format(self, app, client, caplog):
        """Verify timestamp field is ISO 8601 format."""
        from datetime import datetime

        with caplog.at_level(logging.INFO, logger="request_logger"):
            client.get("/api/v1/health")

        log_records = [r for r in caplog.records if r.name == "request_logger"]
        fields = log_records[-1].json_fields
        # Should parse without error
        datetime.fromisoformat(fields["timestamp"])
