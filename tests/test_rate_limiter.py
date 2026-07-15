"""Tests for rate limiting middleware.

Validates: Requirements 3.1, 3.2, 3.3
"""

import pytest
from flask import Flask

from app.middleware.rate_limiter import (
    _extract_retry_after,
    rate_limit_login,
    rate_limit_register,
    register_rate_limit_handler,
)


class TestRateLimiterDecorators:
    """Test that rate limit decorators are properly configured."""

    def test_rate_limit_login_is_callable(self):
        """rate_limit_login decorator is a callable limiter."""
        assert callable(rate_limit_login)

    def test_rate_limit_register_is_callable(self):
        """rate_limit_register decorator is a callable limiter."""
        assert callable(rate_limit_register)

    def test_register_rate_limit_handler_is_callable(self):
        """register_rate_limit_handler accepts an app without error."""
        app = Flask(__name__)
        # Should not raise
        register_rate_limit_handler(app)


class TestExtractRetryAfter:
    """Test the _extract_retry_after helper."""

    def test_extracts_retry_after_attribute(self):
        """Extracts retry_after from error with attribute."""

        class FakeError:
            retry_after = 60

        result = _extract_retry_after(FakeError())
        assert result == 60

    def test_returns_none_when_no_retry_after(self):
        """Returns None when error has no retry_after info."""

        class FakeError:
            pass

        result = _extract_retry_after(FakeError())
        assert result is None

    def test_converts_retry_after_to_int(self):
        """Converts float retry_after to integer seconds."""

        class FakeError:
            retry_after = 42.7

        result = _extract_retry_after(FakeError())
        assert result == 42
        assert isinstance(result, int)


class TestRateLimitErrorHandler:
    """Test that 429 responses follow the standard error format."""

    def test_429_error_handler_registered(self, app):
        """The 429 error handler is registered on the app."""
        # Flask stores error handlers by code
        assert 429 in app.error_handler_spec.get(None, {})

    def test_429_response_format(self, app):
        """429 error handler returns structured JSON with correct code."""
        with app.test_client() as client:
            # Directly invoke the error handler by aborting with 429
            @app.route("/test-abort-429")
            def trigger_429():
                from flask import abort
                abort(429)

            resp = client.get("/test-abort-429")
            assert resp.status_code == 429

            data = resp.get_json()
            assert data["success"] is False
            assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
            assert data["error"]["details"] is None

    def test_429_error_message_present(self, app):
        """429 error response includes a human-readable message."""
        with app.test_client() as client:
            @app.route("/test-abort-429-msg")
            def trigger_429_msg():
                from flask import abort
                abort(429)

            resp = client.get("/test-abort-429-msg")
            data = resp.get_json()
            assert "message" in data["error"]
            assert len(data["error"]["message"]) > 0


class TestRateLimitConfig:
    """Test that rate limit config values are correct."""

    def test_login_rate_limit_config(self, app):
        """Login rate limit defaults to 5/minute (Requirement 3.1)."""
        assert app.config["RATELIMIT_LOGIN"] == "5/minute"

    def test_register_rate_limit_config(self, app):
        """Registration rate limit defaults to 3/minute (Requirement 3.1)."""
        assert app.config["RATELIMIT_REGISTER"] == "3/minute"

    def test_default_rate_limit_config(self, app):
        """Global default rate limit is 200/hour (Requirement 3.3)."""
        assert app.config["RATELIMIT_DEFAULT"] == "200/hour"

    def test_rate_limit_storage_uri_configured(self, app):
        """Rate limit storage uses Redis backend."""
        assert "redis" in app.config["RATELIMIT_STORAGE_URI"]
