"""Booking, BookingStatusHistory, BookingScout, and BookingDriver models.

Validates: Requirements 7.1, 7.4, 7.6, 9.3, 10.2
- 7.1: Multi-step booking flow (select package, dates, travellers, hotel, transport, add-ons, review, payment)
- 7.4: Booking status tracking with full lifecycle (draft → pending_payment → confirmed → in_progress → completed/cancelled/refunded)
- 7.6: Auto-generated unique booking numbers for reference
- 9.3: Admin assigns scouts to confirmed bookings
- 10.2: Admin assigns drivers to confirmed bookings with conflict detection
"""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.models.base import AuditMixin


class BookingStatus(enum.Enum):
    """Enumeration of booking lifecycle statuses."""

    draft = "draft"
    pending_payment = "pending_payment"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    refunded = "refunded"


class Booking(AuditMixin, db.Model):
    """Booking model representing a customer's travel booking.

    Tracks the full lifecycle from draft creation through payment,
    confirmation, trip execution, and completion/cancellation.
    Supports soft delete via AuditMixin.
    """

    __tablename__ = "bookings"

    booking_number = db.Column(
        db.String(20), unique=True, nullable=False, index=True
    )
    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    package_id = db.Column(
        db.String(36),
        db.ForeignKey("packages.id"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum(BookingStatus, name="booking_status_enum"),
        nullable=False,
        default=BookingStatus.draft,
        index=True,
    )
    travel_start_date = db.Column(db.Date, nullable=False)
    travel_end_date = db.Column(db.Date, nullable=False)
    num_travellers = db.Column(db.Integer, nullable=False)
    traveller_type = db.Column(db.String(50), nullable=False)
    hotel_preference_id = db.Column(
        db.String(36),
        db.ForeignKey("hotels.id"),
        nullable=True,
    )
    room_type_id = db.Column(
        db.String(36),
        db.ForeignKey("room_types.id"),
        nullable=True,
    )
    transport_preferences = db.Column(db.JSON, nullable=True)
    add_ons = db.Column(db.JSON, nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=True)
    discount_amount = db.Column(db.Numeric(12, 2), default=0.00)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=True)
    coupon_id = db.Column(
        db.String(36),
        db.ForeignKey("coupons.id"),
        nullable=True,
    )
    special_requests = db.Column(db.Text, nullable=True)

    # Relationships
    status_history = db.relationship(
        "BookingStatusHistory",
        backref="booking",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    booking_scouts = db.relationship(
        "BookingScout",
        backref="booking",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    booking_drivers = db.relationship(
        "BookingDriver",
        backref="booking",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Booking {self.booking_number}>"


class BookingStatusHistory(db.Model):
    """Tracks booking status transitions for audit purposes.

    Records each status change with who made the change and optional notes.
    """

    __tablename__ = "booking_status_history"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )
    from_status = db.Column(db.String(30), nullable=True)
    to_status = db.Column(db.String(30), nullable=False)
    changed_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<BookingStatusHistory {self.from_status} → {self.to_status}>"


class BookingScout(db.Model):
    """Associates a scout with a booking.

    Tracks which scout is assigned to guide a booking, when, and by whom.
    A scout can only be assigned once per booking (unique constraint).
    """

    __tablename__ = "booking_scouts"
    __table_args__ = (
        db.UniqueConstraint(
            "booking_id", "scout_id", name="uq_booking_scout"
        ),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )
    scout_id = db.Column(
        db.String(36),
        db.ForeignKey("scouts.id"),
        nullable=False,
        index=True,
    )
    assigned_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    assigned_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    def __repr__(self):
        return f"<BookingScout booking={self.booking_id} scout={self.scout_id}>"


class BookingDriver(db.Model):
    """Associates a driver with a booking.

    Tracks which driver is assigned to a booking, when, and by whom.
    A driver can only be assigned once per booking (unique constraint).
    """

    __tablename__ = "booking_drivers"
    __table_args__ = (
        db.UniqueConstraint(
            "booking_id", "driver_id", name="uq_booking_driver"
        ),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )
    driver_id = db.Column(
        db.String(36),
        db.ForeignKey("drivers.id"),
        nullable=False,
        index=True,
    )
    assigned_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    assigned_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    def __repr__(self):
        return f"<BookingDriver booking={self.booking_id} driver={self.driver_id}>"
