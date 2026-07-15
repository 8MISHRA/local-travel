"""Notification model for user alerts and messaging.

Validates: Requirement 19.1
- 19.1: In-app and email notifications for booking updates, promotions,
  and system alerts with read/unread tracking.
"""

import enum
from datetime import datetime, timezone
import uuid

from app.extensions import db


class DeliveryChannel(enum.Enum):
    """Enumeration of notification delivery channels."""

    in_app = "in_app"
    email = "email"


class Notification(db.Model):
    """Notification model for user-facing alerts and messages.

    Supports multiple delivery channels and tracks read status
    with timestamps. Uses reference_type/reference_id for polymorphic
    linking to related entities (bookings, payments, etc.).
    """

    __tablename__ = "notifications"

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
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    reference_type = db.Column(db.String(50), nullable=True)
    reference_id = db.Column(db.String(36), nullable=True)
    delivery_channel = db.Column(
        db.Enum(DeliveryChannel, name="delivery_channel_enum"),
        nullable=False,
        default=DeliveryChannel.in_app,
    )
    is_read = db.Column(
        db.Boolean, nullable=False, default=False, index=True
    )
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<Notification {self.title} ({self.notification_type})>"
