"""Global error handlers for the Flask application.

Registers handlers that convert exceptions into the standard API
error response format.

Validates: Requirements 21.2, 21.3, 21.4
"""

import traceback

from flask import current_app, jsonify

from app.utils.exceptions import AppError


def register_error_handlers(app):
    """Register global error handlers on the Flask app.

    Handles:
        - AppError subclasses: returns structured error with appropriate status code.
        - Unhandled exceptions: logs full traceback, returns generic 500 response.
        - Common HTTP errors (404, 405, 429): returns structured error responses.

    Args:
        app: Flask application instance.
    """

    @app.errorhandler(AppError)
    def handle_app_error(error):
        """Handle all custom AppError exceptions."""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response, error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
                "details": None,
            },
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The HTTP method is not allowed for this endpoint.",
                "details": None,
            },
        }), 405

    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle 429 Rate Limit Exceeded errors.

        Includes Retry-After header as required by Requirement 3.2.
        """
        from app.middleware.rate_limiter import _extract_retry_after

        retry_after = _extract_retry_after(error)
        response = jsonify({
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Please try again later.",
                "details": None,
            },
        })
        response.status_code = 429
        if retry_after:
            response.headers["Retry-After"] = str(retry_after)
        return response, 429

    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        """Handle all unhandled exceptions.

        Logs the full traceback for debugging but returns a generic
        error message to avoid leaking internal details (Requirement 21.4).
        """
        current_app.logger.error(
            "Unhandled exception: %s\n%s",
            str(error),
            traceback.format_exc(),
        )
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "details": None,
            },
        }), 500
