"""Authentication middleware with JWT validation and role-based access control.

Provides the `auth_required` decorator that validates Bearer tokens,
extracts user identity into Flask's `g` context, and enforces
endpoint-level role authorization.

Validates: Requirements 4.2, 4.3, 4.4
"""

from functools import wraps

import jwt
from flask import current_app, g, request

from app.utils.response import error_response


def auth_required(roles=None):
    """Decorator that enforces JWT authentication and optional role-based access.

    Extracts the Bearer token from the Authorization header, decodes it using
    the configured JWT_SECRET with HS256, verifies the token type is "access",
    and stores user_id and role in flask.g for downstream use.

    Args:
        roles: Optional list of allowed role strings. If provided, the
            authenticated user's role must be in this list or a 403 is returned.

    Returns:
        Decorated function that checks auth before executing the view.

    Usage:
        @auth_required()
        def protected_endpoint():
            user_id = g.current_user_id
            ...

        @auth_required(roles=["admin", "super_admin"])
        def admin_only_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract Bearer token from Authorization header
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

            if not token:
                return error_response(
                    "UNAUTHORIZED",
                    "Missing authentication token",
                    status_code=401,
                )

            try:
                payload = jwt.decode(
                    token,
                    current_app.config["JWT_SECRET"],
                    algorithms=[current_app.config.get("JWT_ALGORITHM", "HS256")],
                )

                # Verify this is an access token, not a refresh token
                if payload.get("type") != "access":
                    raise jwt.InvalidTokenError("Token is not an access token")

                # Store user context in flask.g for use in views/services
                g.current_user_id = payload["sub"]
                g.current_user_role = payload["role"]

            except jwt.ExpiredSignatureError:
                return error_response(
                    "TOKEN_EXPIRED",
                    "Access token has expired",
                    status_code=401,
                )
            except (jwt.InvalidTokenError, KeyError):
                return error_response(
                    "INVALID_TOKEN",
                    "Invalid access token",
                    status_code=401,
                )

            # Enforce role-based access if roles are specified
            if roles and g.current_user_role not in roles:
                return error_response(
                    "FORBIDDEN",
                    "Insufficient permissions",
                    status_code=403,
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator
