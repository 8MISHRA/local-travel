"""Authentication request/response schemas for validation and serialization.

Validates: Requirements 1.1, 1.4, 1.5, 2.1
- 1.1: Registration with email, password, full_name, phone
- 1.4: Validation errors with field-level details (HTTP 422)
- 1.5: Minimum password length of 8 characters
- 2.1: Login with email and password
"""

from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    """Schema for user registration requests.

    Required fields:
        email: Valid email address
        password: Minimum 8 characters (Requirement 1.5)
        full_name: User's full name (non-empty)
        phone: Phone number (non-empty)
    """

    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Invalid email address."},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, error="Password must be at least 8 characters long."),
        error_messages={"required": "Password is required."},
        load_only=True,
    )
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=150, error="Full name must be between 1 and 150 characters."),
        error_messages={"required": "Full name is required."},
    )
    phone = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20, error="Phone number must be between 1 and 20 characters."),
        error_messages={"required": "Phone number is required."},
    )


class LoginSchema(Schema):
    """Schema for user login requests.

    Required fields:
        email: Valid email address
        password: Non-empty password string
    """

    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required.", "invalid": "Invalid email address."},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Password is required."),
        error_messages={"required": "Password is required."},
        load_only=True,
    )


class TokenRefreshSchema(Schema):
    """Schema for token refresh requests.

    Required fields:
        refresh_token: The refresh token JWT string
    """

    refresh_token = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Refresh token is required."),
        error_messages={"required": "Refresh token is required."},
    )


class UserResponseSchema(Schema):
    """Schema for serializing user data in responses."""

    id = fields.String(dump_only=True)
    email = fields.Email(dump_only=True)
    full_name = fields.String(dump_only=True)
    phone = fields.String(dump_only=True)
    role = fields.String(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class AuthResponseSchema(Schema):
    """Schema for auth response (tokens + user data)."""

    access_token = fields.String(dump_only=True)
    refresh_token = fields.String(dump_only=True)
    user = fields.Nested(UserResponseSchema, dump_only=True)
