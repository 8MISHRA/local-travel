"""Tests for User and RefreshToken models.

Validates: Requirements 1.1, 2.1, 4.1
"""

from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def db_session():
    """Provide a clean database session for model testing using SQLite."""
    from flask import Flask
    from app.extensions import db

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True

    db.init_app(app)

    with app.app_context():
        # Import models to register them with SQLAlchemy
        from app.models.user import User, RefreshToken  # noqa: F401

        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


class TestUserModel:
    """Tests for the User model."""

    def test_user_creation_with_defaults(self, db_session):
        """User created with required fields gets correct defaults."""
        from app.models.user import User, UserRole

        user = User(
            email="test@example.com",
            password_hash="hashed_password_123",
            full_name="Test User",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert len(user.id) == 36  # UUID format
        assert user.email == "test@example.com"
        assert user.role == UserRole.customer
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.deleted_at is None

    def test_user_role_enum_values(self):
        """All required roles are present in UserRole enum."""
        from app.models.user import UserRole

        expected_roles = [
            "guest", "customer", "scout", "driver",
            "vendor", "hotel_partner", "admin", "super_admin",
        ]
        actual_roles = [r.value for r in UserRole]
        assert set(expected_roles) == set(actual_roles)

    def test_user_email_unique_constraint(self, db_session):
        """Duplicate emails are rejected by the database."""
        from app.models.user import User

        user1 = User(
            email="dup@example.com",
            password_hash="hash1",
            full_name="User One",
            phone="+911111111111",
        )
        user2 = User(
            email="dup@example.com",
            password_hash="hash2",
            full_name="User Two",
            phone="+912222222222",
        )
        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_user_soft_delete(self, db_session):
        """Soft delete sets deleted_at without removing the record."""
        from app.models.user import User

        user = User(
            email="delete@example.com",
            password_hash="hash",
            full_name="Delete Me",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        assert user.is_deleted is False
        user.soft_delete()
        db_session.commit()

        assert user.is_deleted is True
        assert user.deleted_at is not None
        # Record still exists in the database
        found = db_session.get(User, user.id)
        assert found is not None

    def test_user_repr(self, db_session):
        """User repr shows email."""
        from app.models.user import User

        user = User(
            email="repr@example.com",
            password_hash="hash",
            full_name="Repr Test",
            phone="+910000000000",
        )
        assert repr(user) == "<User repr@example.com>"


class TestRefreshTokenModel:
    """Tests for the RefreshToken model."""

    def test_refresh_token_creation(self, db_session):
        """RefreshToken is created with correct fields and FK."""
        from app.models.user import User, RefreshToken

        user = User(
            email="token@example.com",
            password_hash="hash",
            full_name="Token User",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash="unique_hash_value_123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()

        assert token.id is not None
        assert token.user_id == user.id
        assert token.is_revoked is False
        assert token.created_at is not None

    def test_refresh_token_is_valid(self, db_session):
        """Token is valid when not expired and not revoked."""
        from app.models.user import User, RefreshToken

        user = User(
            email="valid@example.com",
            password_hash="hash",
            full_name="Valid User",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash="valid_hash_123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_valid is True
        assert token.is_expired is False

    def test_refresh_token_expired(self, db_session):
        """Expired token reports as invalid."""
        from app.models.user import User, RefreshToken

        user = User(
            email="expired@example.com",
            password_hash="hash",
            full_name="Expired User",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash="expired_hash_123",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_expired is True
        assert token.is_valid is False

    def test_refresh_token_revoke(self, db_session):
        """Revoking a token marks it as invalid."""
        from app.models.user import User, RefreshToken

        user = User(
            email="revoke@example.com",
            password_hash="hash",
            full_name="Revoke User",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        token = RefreshToken(
            user_id=user.id,
            token_hash="revoke_hash_123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        db_session.commit()

        assert token.is_valid is True
        token.revoke()
        db_session.commit()

        assert token.is_revoked is True
        assert token.is_valid is False

    def test_user_refresh_tokens_relationship(self, db_session):
        """User.refresh_tokens relationship returns associated tokens."""
        from app.models.user import User, RefreshToken

        user = User(
            email="rel@example.com",
            password_hash="hash",
            full_name="Rel User",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        t1 = RefreshToken(
            user_id=user.id,
            token_hash="hash_1",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        t2 = RefreshToken(
            user_id=user.id,
            token_hash="hash_2",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add_all([t1, t2])
        db_session.commit()

        assert user.refresh_tokens.count() == 2

    def test_token_hash_unique_constraint(self, db_session):
        """Duplicate token_hash values are rejected."""
        from app.models.user import User, RefreshToken

        user = User(
            email="unique@example.com",
            password_hash="hash",
            full_name="Unique User",
            phone="+911234567890",
        )
        db_session.add(user)
        db_session.commit()

        t1 = RefreshToken(
            user_id=user.id,
            token_hash="duplicate_hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        t2 = RefreshToken(
            user_id=user.id,
            token_hash="duplicate_hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(t1)
        db_session.commit()

        db_session.add(t2)
        with pytest.raises(Exception):
            db_session.commit()
