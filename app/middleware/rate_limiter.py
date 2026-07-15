"""Rate limiting middleware using Flask-Limiter with Redis backend.

Provides endpoint-specific rate limit decorators for authentication routes
and a handler for 429 Too Many Requests responses.

Validates: Requirements 3.1, 3.2, 3.3
"""

from flask import current_app

from app.extensions import limiter


def _get_login_limit():
    """Retrieve the login rate limit string from app config.

    Returns:
        Rate limit string (e.g. '5/minute').
    """
    return current_app.config.get("RATELIMIT_LOGIN", "5/minute")


def _get_register_limit():
    """Retrieve the registration rate limit string from app config.

    Returns:
        Rate limit string (e.g. '3/minute').
    """
    return current_app.config.get("RATELIMIT_REGISTER", "3/minute")


# Decorators for auth-specific rate limits
rate_limit_login = limiter.limit(_get_login_limit)
rate_limit_register = limiter.limit(_get_register_limit)


def _extract_retry_after(error):
    """Extract Retry-After value from a rate limit error.

    Flask-Limiter attaches the retry_after attribute to the
    RateLimitExceeded exception or includes it in the response headers.

    Args:
        error: The 429 error/exception instance.

    Returns:
        Integer seconds until the client can retry, or None if unavailable.
    """
    # Flask-Limiter's RateLimitExceeded stores retry_after on the description
    # or as an attribute depending on the version.
    retry_after = getattr(error, "retry_after", None)
    if retry_after is not None:
        return int(retry_after)

    # Some versions store it in the description or response headers
    description = getattr(error, "description", None)
    if description and hasattr(description, "headers"):
        return description.headers.get("Retry-After")

    return None


def register_rate_limit_handler(app):
    """Register the 429 rate limit error handler on the Flask app.

    This is called during app initialization to ensure rate limit
    exceeded responses follow the standard error format with Retry-After
    header.

    Args:
        app: Flask application instance.
    """
    # The 429 handler is already registered in app/errors.py via
    # register_error_handlers(). This function exists as an explicit
    # integration point if needed for additional rate-limit setup
    # (e.g., custom on_breach callbacks).
    pass
