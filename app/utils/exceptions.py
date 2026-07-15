"""Custom exception hierarchy for the application.

Provides structured error classes that map to specific HTTP status codes
and produce consistent error responses.

Validates: Requirements 21.1, 21.2, 21.3
"""


class AppError(Exception):
    """Base application error.

    All custom exceptions inherit from this class.
    Each carries an error code, human-readable message,
    optional details dict, and the corresponding HTTP status code.
    """

    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message="An unexpected error occurred.", details=None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self):
        """Serialize the error to the standard API error format."""
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


class NotFoundError(AppError):
    """Resource not found (HTTP 404)."""

    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, message="The requested resource was not found.", details=None):
        super().__init__(message, details)


class ValidationError(AppError):
    """Validation failed (HTTP 422)."""

    status_code = 422
    code = "VALIDATION_ERROR"

    def __init__(self, message="Validation failed.", details=None):
        super().__init__(message, details)


class ConflictError(AppError):
    """Resource conflict (HTTP 409)."""

    status_code = 409
    code = "CONFLICT"

    def __init__(self, message="A conflict occurred with the current state of the resource.", details=None):
        super().__init__(message, details)


class UnauthorizedError(AppError):
    """Authentication required (HTTP 401)."""

    status_code = 401
    code = "UNAUTHORIZED"

    def __init__(self, message="Authentication is required.", details=None):
        super().__init__(message, details)


class ForbiddenError(AppError):
    """Access denied (HTTP 403)."""

    status_code = 403
    code = "FORBIDDEN"

    def __init__(self, message="You do not have permission to perform this action.", details=None):
        super().__init__(message, details)


class RateLimitError(AppError):
    """Rate limit exceeded (HTTP 429)."""

    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message="Rate limit exceeded. Please try again later.", details=None):
        super().__init__(message, details)


class InvalidStateTransitionError(AppError):
    """Invalid state transition for a booking or similar state machine (HTTP 422)."""

    status_code = 422
    code = "INVALID_STATE_TRANSITION"

    def __init__(self, message="The requested state transition is not allowed.", details=None):
        super().__init__(message, details)
