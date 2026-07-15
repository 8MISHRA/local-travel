"""Property-based tests for the authentication system.

**Validates: Requirements 1.2, 1.3, 1.4, 1.5, 2.2, 2.3, 2.4, 2.5**

Property 1: Password is never stored in plaintext
- For any registration with password P, the stored password_hash != P.

Property 2: Registration input validation rejects invalid payloads
- Missing/invalid fields always get 422.

Property 3: Duplicate email registration rejection
- Existing email always returns 409.

Property 4: Login with incorrect credentials returns generic error
- Wrong email/password always returns same generic 401 message
  (doesn't reveal which field is wrong).

Property 5: Refresh token rotation invalidates old token
- After refresh, old token is always rejected.

Property 6: Logout invalidates refresh token
- After logout, the token is always rejected.
"""

import os
import uuid
from contextlib import contextmanager
from datetime import timedelta

import pytest
from hypothesis import given, settings, assume, HealthCheck, Phase
from hypothesis import strategies as st

os.environ["FLASK_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db


# --- Strategies ---

# Valid email strategy
valid_emails = st.emails()

# Valid passwords (8-100 chars, printable)
valid_passwords = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")),
    min_size=8,
    max_size=100,
).filter(lambda p: len(p.strip()) >= 8)

# Invalid passwords (too short: 1-7 chars)
invalid_passwords = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=1,
    max_size=7,
)

# Full names (1-150 chars)
valid_full_names = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
    min_size=1,
    max_size=150,
).filter(lambda n: len(n.strip()) >= 1)

# Phone numbers (1-20 chars)
valid_phones = st.text(
    alphabet=st.characters(whitelist_categories=("N",), whitelist_characters="+-() "),
    min_size=1,
    max_size=20,
).filter(lambda p: len(p.strip()) >= 1)


# --- Helper context manager ---

@contextmanager
def fresh_app_context():
    """Create a fresh Flask app with SQLite in-memory DB for each test invocation."""
    app = create_app("testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET"] = "test-secret-key-for-property-tests"
    app.config["JWT_ALGORITHM"] = "HS256"
    app.config["JWT_ACCESS_EXPIRY"] = timedelta(minutes=15)
    app.config["JWT_REFRESH_EXPIRY"] = timedelta(hours=1)

    with app.app_context():
        db.create_all()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()


# --- Property 1: Password is never stored in plaintext ---

class TestPasswordNeverStoredInPlaintext:
    """Property 1: For any registration with password P, stored password_hash != P.

    **Validates: Requirements 1.3**
    """

    @given(
        password=valid_passwords,
        email=valid_emails,
        full_name=valid_full_names,
        phone=valid_phones,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_password_hash_differs_from_plaintext(self, password, email, full_name, phone):
        """The stored password_hash is never equal to the plaintext password."""
        with fresh_app_context() as app:
            client = app.test_client()
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "phone": phone,
                },
            )

            if response.status_code == 201:
                # Check that password_hash in DB differs from plaintext
                from app.models.user import User
                user = db.session.query(User).filter_by(email=email).first()
                assert user is not None
                assert user.password_hash != password
                # Verify it's a bcrypt hash (starts with $2b$)
                assert user.password_hash.startswith("$2b$")


# --- Property 2: Registration input validation rejects invalid payloads ---

class TestRegistrationInputValidation:
    """Property 2: Missing/invalid fields always get 422.

    **Validates: Requirements 1.4, 1.5**
    """

    @given(
        email=valid_emails,
        full_name=valid_full_names,
        phone=valid_phones,
        password=invalid_passwords,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_short_password_returns_422(self, email, full_name, phone, password):
        """Passwords shorter than 8 characters are rejected with 422."""
        with fresh_app_context() as app:
            client = app.test_client()
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "phone": phone,
                },
            )
            assert response.status_code == 422
            body = response.get_json()
            assert body["success"] is False
            assert body["error"]["code"] == "VALIDATION_ERROR"

    @given(
        password=valid_passwords,
        full_name=valid_full_names,
        phone=valid_phones,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_missing_email_returns_422(self, password, full_name, phone):
        """Requests missing the email field are rejected with 422."""
        with fresh_app_context() as app:
            client = app.test_client()
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "password": password,
                    "full_name": full_name,
                    "phone": phone,
                },
            )
            assert response.status_code == 422
            body = response.get_json()
            assert body["success"] is False
            assert body["error"]["code"] == "VALIDATION_ERROR"

    @given(
        email=valid_emails,
        full_name=valid_full_names,
        phone=valid_phones,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_missing_password_returns_422(self, email, full_name, phone):
        """Requests missing the password field are rejected with 422."""
        with fresh_app_context() as app:
            client = app.test_client()
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "full_name": full_name,
                    "phone": phone,
                },
            )
            assert response.status_code == 422
            body = response.get_json()
            assert body["success"] is False

    @given(
        email=valid_emails,
        password=valid_passwords,
        phone=valid_phones,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_missing_full_name_returns_422(self, email, password, phone):
        """Requests missing the full_name field are rejected with 422."""
        with fresh_app_context() as app:
            client = app.test_client()
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "phone": phone,
                },
            )
            assert response.status_code == 422
            body = response.get_json()
            assert body["success"] is False


# --- Property 3: Duplicate email registration rejection ---

class TestDuplicateEmailRejection:
    """Property 3: Existing email always returns 409.

    **Validates: Requirements 1.2**
    """

    @given(
        email=valid_emails,
        password1=valid_passwords,
        password2=valid_passwords,
        full_name=valid_full_names,
        phone=valid_phones,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_duplicate_email_returns_409(self, email, password1, password2,
                                         full_name, phone):
        """Registering with an already-registered email always returns 409."""
        with fresh_app_context() as app:
            client = app.test_client()

            # First registration should succeed
            response1 = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password1,
                    "full_name": full_name,
                    "phone": phone,
                },
            )
            assert response1.status_code == 201

            # Second registration with same email should return 409
            response2 = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password2,
                    "full_name": full_name,
                    "phone": phone,
                },
            )
            assert response2.status_code == 409
            body = response2.get_json()
            assert body["success"] is False
            assert body["error"]["code"] == "CONFLICT"


# --- Property 4: Login with incorrect credentials returns generic error ---

class TestLoginGenericErrorMessage:
    """Property 4: Wrong email/password always returns same generic 401 message.

    **Validates: Requirements 2.2**
    """

    @given(
        email=valid_emails,
        password=valid_passwords,
        wrong_password=valid_passwords,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_wrong_password_returns_generic_401(self, email, password, wrong_password):
        """Login with wrong password returns generic 401 without revealing which field is wrong."""
        assume(password != wrong_password)

        with fresh_app_context() as app:
            client = app.test_client()

            # Register user first
            reg_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": "Test User",
                    "phone": "1234567890",
                },
            )
            assert reg_response.status_code == 201

            # Attempt login with wrong password
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": wrong_password,
                },
            )
            assert login_response.status_code == 401
            body = login_response.get_json()
            assert body["success"] is False
            # Message should be generic - not specifically revealing which field is wrong
            error_msg = body["error"]["message"]
            assert "Invalid email or password" in error_msg

    @given(
        email=valid_emails,
        wrong_email=valid_emails,
        password=valid_passwords,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_nonexistent_email_returns_generic_401(self, email, wrong_email, password):
        """Login with non-existent email returns same generic 401 message."""
        assume(email != wrong_email)

        with fresh_app_context() as app:
            client = app.test_client()

            # Register user
            reg_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": "Test User",
                    "phone": "1234567890",
                },
            )
            assert reg_response.status_code == 201

            # Login with wrong email
            login_response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": wrong_email,
                    "password": password,
                },
            )
            assert login_response.status_code == 401
            body = login_response.get_json()
            assert body["success"] is False
            error_msg = body["error"]["message"]
            # The error message should be the same generic message
            assert "Invalid email or password" in error_msg

    @given(
        email=valid_emails,
        password=valid_passwords,
        wrong_password=valid_passwords,
        wrong_email=valid_emails,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_wrong_email_and_wrong_password_return_same_message(
        self, email, password, wrong_password, wrong_email
    ):
        """Both wrong-email and wrong-password produce the same error message."""
        assume(password != wrong_password)
        assume(email != wrong_email)

        with fresh_app_context() as app:
            client = app.test_client()

            # Register user
            reg_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": "Test User",
                    "phone": "1234567890",
                },
            )
            assert reg_response.status_code == 201

            # Login with wrong password
            resp_wrong_pass = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": wrong_password},
            )

            # Login with wrong email
            resp_wrong_email = client.post(
                "/api/v1/auth/login",
                json={"email": wrong_email, "password": password},
            )

            assert resp_wrong_pass.status_code == 401
            assert resp_wrong_email.status_code == 401

            body_pass = resp_wrong_pass.get_json()
            body_email = resp_wrong_email.get_json()

            # Both should return the exact same error message
            assert body_pass["error"]["message"] == body_email["error"]["message"]


# --- Property 5: Refresh token rotation invalidates old token ---

class TestRefreshTokenRotation:
    """Property 5: After refresh, old token is always rejected.

    **Validates: Requirements 2.3, 2.4**
    """

    @given(
        email=valid_emails,
        password=valid_passwords,
        full_name=valid_full_names,
        phone=valid_phones,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_old_refresh_token_rejected_after_rotation(self, email, password,
                                                        full_name, phone):
        """After a successful token refresh, the old refresh token is rejected."""
        with fresh_app_context() as app:
            client = app.test_client()

            # Register user to get initial tokens
            reg_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "phone": phone,
                },
            )
            assert reg_response.status_code == 201
            reg_data = reg_response.get_json()
            old_refresh_token = reg_data["data"]["refresh_token"]

            # Refresh to get new tokens
            refresh_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": old_refresh_token},
            )
            assert refresh_response.status_code == 200
            refresh_data = refresh_response.get_json()
            new_refresh_token = refresh_data["data"]["refresh_token"]

            # The new token should be different
            assert new_refresh_token != old_refresh_token

            # The old token should now be rejected
            replay_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": old_refresh_token},
            )
            assert replay_response.status_code == 401
            replay_body = replay_response.get_json()
            assert replay_body["success"] is False


# --- Property 6: Logout invalidates refresh token ---

class TestLogoutInvalidatesToken:
    """Property 6: After logout, the token is always rejected.

    **Validates: Requirements 2.5**
    """

    @given(
        email=valid_emails,
        password=valid_passwords,
        full_name=valid_full_names,
        phone=valid_phones,
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_refresh_token_rejected_after_logout(self, email, password,
                                                  full_name, phone):
        """After logout, the refresh token cannot be used for refresh."""
        with fresh_app_context() as app:
            client = app.test_client()

            # Register user to get tokens
            reg_response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": full_name,
                    "phone": phone,
                },
            )
            assert reg_response.status_code == 201
            reg_data = reg_response.get_json()
            refresh_token = reg_data["data"]["refresh_token"]

            # Logout with the refresh token
            logout_response = client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": refresh_token},
            )
            assert logout_response.status_code == 200

            # Attempt to use the revoked token for refresh
            refresh_response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert refresh_response.status_code == 401
            body = refresh_response.get_json()
            assert body["success"] is False
