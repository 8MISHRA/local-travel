"""Base model mixin providing audit fields for all database models.

Validates: Requirements 23.1, 23.2
- 23.1: All tables include created_at and updated_at timestamp columns
- 23.2: Soft delete implementation via deleted_at timestamp
"""

from datetime import datetime, timezone
import uuid

from app.extensions import db


class AuditMixin:
    """Mixin providing common audit fields for all models.

    Adds:
        id: UUID primary key (string format for PostgreSQL compatibility)
        created_at: Timestamp of record creation (UTC)
        updated_at: Timestamp of last update (UTC, auto-updates on change)
        deleted_at: Timestamp of soft deletion (NULL if not deleted)
    """

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    @property
    def is_deleted(self):
        """Return True if the record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self):
        """Mark this record as soft-deleted by setting deleted_at to current UTC time."""
        self.deleted_at = datetime.now(timezone.utc)
