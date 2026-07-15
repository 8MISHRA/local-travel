"""User and RefreshToken models.

Validates: Requirements 1.1, 2.1, 4.1
- 1.1: User registration with email, password, full_name, phone
- 2.1: Authentication with access/refresh token pairs
- 4.1: Role-based access control with defined role set
"""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.models.base import AuditMixin


class UserRole(enum.Enum):
    """Enumeration of platform user roles.

    Validates: Requirement 4.1 - Platform supports Guest, Customer, Scout,
    Driver, Vendor, Hotel_Partner, Admin, and Super_Admin roles.
    """

    guest = "guest"
    customer = "customer"
    scout = "scout"
    driver = "driver"
    vendor = "vendor"
    hotel_partner = "hotel_partner"
    admin = "admin"
    super_admin = "super_admin"


class User(AuditMixin, db.Model):
    """User account model.

    Stores registered users with role-based access control and soft delete.
    Inherits id, created_at, updated_at, deleted_at from AuditMixin.
    """

    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(
        db.Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.customer,
        index=True,
    )
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    refresh_tokens = db.relationship(
        "RefreshToken",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        db.Index("ix_users_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return f"<User {self.email}>"


class RefreshToken(db.Model):
    """Refresh token model for managing user sessions.

    Validates: Requirement 2.1 - Access/refresh token pair authentication.
    Stores hashed refresh tokens with expiry and revocation tracking.
    """

    __tablename__ = "refresh_tokens"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    token_hash = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="refresh_tokens")

    @property
    def is_expired(self):
        """Return True if the token has passed its expiration time."""
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        # Handle timezone-naive datetimes (e.g. from SQLite)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    @property
    def is_valid(self):
        """Return True if the token is neither revoked nor expired."""
        return not self.is_revoked and not self.is_expired

    def revoke(self):
        """Mark this refresh token as revoked."""
        self.is_revoked = True

    def __repr__(self):
        return f"<RefreshToken user_id={self.user_id}>"
