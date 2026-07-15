"""Tests for authentication middleware and RBAC utilities.

Validates: Requirements 4.2, 4.3, 4.4
"""

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from flask import Flask, g

from app.middleware.auth_middleware import auth_required
from app.middleware.rbac_middleware import (
    ADMIN_ROLES,
    ROLES,
    STAFF_ROLES,
    check_permission,
    get_current_user_id,
    get_current_user_role,
    has_any_role,
    has_minimum_role,
    has_role,
    is_admin,
    is_owner_or_admin,
    is_super_admin,
    is_valid_role,
)
from app.utils.response import error_response

JWT_SECRET = "test-secret-key"


@pytest.fixture
def app():
    """Create a minimal Flask app for testing middleware."""
    app = Flask(__name__)
    app.config["JWT_SECRET"] = JWT_SECRET
    app.config["JWT_ALGORITHM"] = "HS256"
    app.config["TESTING"] = True

    @app.route("/protected")
    @auth_required()
    def protected():
        return {"user_id": g.current_user_id, "role": g.current_user_role}

    @app.route("/admin-only")
    @auth_required(roles=["admin", "super_admin"])
    def admin_only():
        return {"message": "admin access granted"}

    @app.route("/multi-role")
    @auth_required(roles=["customer", "admin", "super_admin"])
    def multi_role():
        return {"message": "access granted"}

    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def generate_token(payload_overrides=None, secret=JWT_SECRET):
    """Helper to generate a JWT token with default claims."""
    payload = {
        "sub": "user-123",
        "role": "customer",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    if payload_overrides:
        payload.update(payload_overrides)
    return jwt.encode(payload, secret, algorithm="HS256")


class TestAuthRequired:
    """Tests for the auth_required decorator."""

    def test_missing_auth_header_returns_401(self, client):
        """Request without Authorization header gets 401."""
        response = client.get("/protected")
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"
        assert "Missing authentication token" in data["error"]["message"]

    def test_empty_bearer_token_returns_401(self, client):
        """Request with empty Bearer token gets 401."""
        response = client.get("/protected", headers={"Authorization": "Bearer "})
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_valid_token_grants_access(self, client):
        """Valid access token allows the request through."""
        token = generate_token()
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["user_id"] == "user-123"
        assert data["role"] == "customer"

    def test_expired_token_returns_401(self, client):
        """Expired token returns TOKEN_EXPIRED error."""
        token = generate_token(
            {"exp": datetime.now(timezone.utc) - timedelta(hours=1)}
        )
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "TOKEN_EXPIRED"

    def test_invalid_signature_returns_401(self, client):
        """Token signed with wrong secret returns INVALID_TOKEN."""
        token = generate_token(secret="wrong-secret")
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_refresh_token_rejected(self, client):
        """Refresh token (type != access) is rejected."""
        token = generate_token({"type": "refresh"})
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_malformed_token_returns_401(self, client):
        """Malformed (non-JWT) token returns INVALID_TOKEN."""
        response = client.get(
            "/protected", headers={"Authorization": "Bearer not-a-valid-jwt"}
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_TOKEN"

    def test_token_missing_sub_returns_401(self, client):
        """Token without 'sub' claim is rejected."""
        payload = {
            "role": "customer",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    def test_token_missing_role_returns_401(self, client):
        """Token without 'role' claim is rejected."""
        payload = {
            "sub": "user-123",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    def test_non_bearer_auth_header_returns_401(self, client):
        """Authorization header without 'Bearer ' prefix is rejected."""
        token = generate_token()
        response = client.get(
            "/protected", headers={"Authorization": f"Basic {token}"}
        )
        assert response.status_code == 401


class TestRoleBasedAccess:
    """Tests for role-based access enforcement."""

    def test_correct_role_grants_access(self, client):
        """User with required role gets access."""
        token = generate_token({"role": "admin"})
        response = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_wrong_role_returns_403(self, client):
        """User without required role gets 403 FORBIDDEN."""
        token = generate_token({"role": "customer"})
        response = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data["error"]["code"] == "FORBIDDEN"
        assert "Insufficient permissions" in data["error"]["message"]

    def test_super_admin_accesses_admin_endpoint(self, client):
        """Super admin can access admin-only endpoints."""
        token = generate_token({"role": "super_admin"})
        response = client.get(
            "/admin-only", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_multi_role_endpoint_accepts_any_listed_role(self, client):
        """Endpoint with multiple roles accepts any matching role."""
        for role in ["customer", "admin", "super_admin"]:
            token = generate_token({"role": role})
            response = client.get(
                "/multi-role", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200


class TestRBACUtilities:
    """Tests for RBAC helper functions."""

    def test_is_valid_role_accepts_known_roles(self):
        """All defined roles are recognized."""
        for role in ["guest", "customer", "scout", "driver", "vendor",
                     "hotel_partner", "admin", "super_admin"]:
            assert is_valid_role(role) is True

    def test_is_valid_role_rejects_unknown_roles(self):
        """Unknown role strings are rejected."""
        assert is_valid_role("unknown") is False
        assert is_valid_role("") is False
        assert is_valid_role("ADMIN") is False  # case-sensitive

    def test_has_role_checks_current_user(self, app):
        """has_role checks against g.current_user_role."""
        with app.test_request_context():
            g.current_user_role = "admin"
            assert has_role("admin") is True
            assert has_role("customer") is False

    def test_has_any_role(self, app):
        """has_any_role checks against a list of roles."""
        with app.test_request_context():
            g.current_user_role = "scout"
            assert has_any_role(STAFF_ROLES) is True
            assert has_any_role(ADMIN_ROLES) is False

    def test_has_minimum_role(self, app):
        """has_minimum_role uses role hierarchy levels."""
        with app.test_request_context():
            g.current_user_role = "admin"
            assert has_minimum_role("customer") is True
            assert has_minimum_role("admin") is True
            assert has_minimum_role("super_admin") is False

    def test_is_admin(self, app):
        """is_admin checks for admin or super_admin."""
        with app.test_request_context():
            g.current_user_role = "admin"
            assert is_admin() is True
            g.current_user_role = "super_admin"
            assert is_admin() is True
            g.current_user_role = "customer"
            assert is_admin() is False

    def test_is_super_admin(self, app):
        """is_super_admin only matches super_admin."""
        with app.test_request_context():
            g.current_user_role = "super_admin"
            assert is_super_admin() is True
            g.current_user_role = "admin"
            assert is_super_admin() is False

    def test_is_owner_or_admin(self, app):
        """is_owner_or_admin grants access to resource owner or admin."""
        with app.test_request_context():
            g.current_user_id = "user-456"
            g.current_user_role = "customer"
            # Owner
            assert is_owner_or_admin("user-456") is True
            # Not owner, not admin
            assert is_owner_or_admin("user-789") is False
            # Admin accessing another user's resource
            g.current_user_role = "admin"
            assert is_owner_or_admin("user-789") is True

    def test_check_permission_returns_none_when_authorized(self, app):
        """check_permission returns None if role is allowed."""
        with app.test_request_context():
            g.current_user_role = "admin"
            result = check_permission(ADMIN_ROLES)
            assert result is None

    def test_check_permission_returns_error_when_unauthorized(self, app):
        """check_permission returns error response if role is not allowed."""
        with app.test_request_context():
            g.current_user_role = "customer"
            result = check_permission(ADMIN_ROLES)
            assert result is not None
            # Result is a tuple (response, status_code)
            response, status_code = result
            assert status_code == 403

    def test_get_current_user_role_without_auth(self, app):
        """get_current_user_role returns None when not authenticated."""
        with app.test_request_context():
            assert get_current_user_role() is None

    def test_get_current_user_id_without_auth(self, app):
        """get_current_user_id returns None when not authenticated."""
        with app.test_request_context():
            assert get_current_user_id() is None
