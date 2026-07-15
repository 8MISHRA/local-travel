"""Authentication routes: register, login, refresh, logout, me.

Validates: Requirements 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5
- 1.1: POST /register creates account, returns tokens
- 1.2: POST /register rejects duplicate email with 409
- 1.4: POST /register rejects invalid fields with 422
- 2.1: POST /login returns access + refresh token pair
- 2.2: POST /login rejects bad credentials with generic 401
- 2.3: POST /refresh issues new token pair, invalidates old
- 2.4: POST /refresh rejects expired/invalid tokens with 401
- 2.5: POST /logout invalidates refresh token
"""

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.auth.schemas import LoginSchema, RegisterSchema, TokenRefreshSchema
from app.middleware.auth_middleware import auth_required
from app.services.auth_service import AuthService
from app.utils.exceptions import AppError
from app.utils.response import error_response, success_response

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account.

    Request body: {email, password, full_name, phone}
    Success: 201 with {access_token, refresh_token, user}
    Errors: 409 (duplicate email), 422 (validation)
    """
    # Validate request body
    schema = RegisterSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    # Delegate to service
    auth_service = AuthService()
    result = auth_service.register(
        email=data["email"],
        password=data["password"],
        full_name=data["full_name"],
        phone=data["phone"],
    )

    return success_response(result, message="Registration successful.", status_code=201)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user with email and password.

    Request body: {email, password}
    Success: 200 with {access_token, refresh_token, user}
    Errors: 401 (invalid credentials), 422 (validation)
    """
    # Validate request body
    schema = LoginSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    # Delegate to service
    auth_service = AuthService()
    result = auth_service.login(
        email=data["email"],
        password=data["password"],
    )

    return success_response(result, message="Login successful.")


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Refresh the access/refresh token pair.

    Request body: {refresh_token}
    Success: 200 with {access_token, refresh_token, user}
    Errors: 401 (invalid/expired/revoked token), 422 (validation)

    Validates: Requirements 2.3, 2.4
    """
    # Validate request body
    schema = TokenRefreshSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    # Delegate to service
    auth_service = AuthService()
    result = auth_service.refresh_tokens(
        refresh_token_str=data["refresh_token"],
    )

    return success_response(result, message="Token refreshed successfully.")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout by invalidating the refresh token.

    Request body: {refresh_token}
    Success: 200 with confirmation message
    Errors: 401 (invalid token), 422 (validation)

    Validates: Requirement 2.5
    """
    # Validate request body
    schema = TokenRefreshSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    # Delegate to service
    auth_service = AuthService()
    auth_service.logout(
        refresh_token_str=data["refresh_token"],
    )

    return success_response(None, message="Logged out successfully.")


@auth_bp.route("/me", methods=["GET"])
@auth_required()
def me():
    """Get the currently authenticated user's profile.

    Requires: Valid access token in Authorization header.
    Success: 200 with user data.
    Errors: 401 (missing/invalid token)
    """
    from flask import g

    from app.extensions import db
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository(db.session)
    user = user_repo.get_by_id(g.current_user_id)

    if not user:
        return error_response(
            "NOT_FOUND",
            "User not found.",
            status_code=404,
        )

    user_data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

    return success_response(user_data, message="Success")
