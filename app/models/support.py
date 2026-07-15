"""SupportTicket and TicketReply models for customer support.

Validates: Requirement 20.1
- 20.1: Support ticket system with priority levels, status tracking,
  and threaded replies between customers and support staff.
"""

import enum
from datetime import datetime, timezone
import uuid

from app.extensions import db


class TicketPriority(enum.Enum):
    """Enumeration of support ticket priority levels."""

    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TicketStatus(enum.Enum):
    """Enumeration of support ticket statuses."""

    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class SupportTicket(db.Model):
    """Support ticket model for customer issue tracking.

    Supports optional linking to a booking and tracks priority
    and status through the resolution lifecycle.
    """

    __tablename__ = "support_tickets"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=True,
        index=True,
    )
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(
        db.Enum(TicketPriority, name="ticket_priority_enum"),
        nullable=False,
        default=TicketPriority.medium,
    )
    status = db.Column(
        db.Enum(TicketStatus, name="ticket_status_enum"),
        nullable=False,
        default=TicketStatus.open,
        index=True,
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

    # Relationships
    replies = db.relationship(
        "TicketReply",
        backref="ticket",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<SupportTicket {self.subject} ({self.status.value})>"


class TicketReply(db.Model):
    """Reply within a support ticket thread.

    Tracks which user authored the reply and when it was created.
    """

    __tablename__ = "ticket_replies"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    ticket_id = db.Column(
        db.String(36),
        db.ForeignKey("support_tickets.id"),
        nullable=False,
        index=True,
    )
    author_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<TicketReply ticket={self.ticket_id} author={self.author_id}>"
