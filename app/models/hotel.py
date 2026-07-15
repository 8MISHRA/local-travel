"""Hotel, RoomType, and RoomAvailability models.

Validates: Requirements 8.1, 8.2, 8.3
- 8.1: Hotel record with name, address, star rating, amenities, contact details,
       and partner user association.
- 8.2: Room type with name, capacity, base price, description, and amenities
       for a hotel.
- 8.3: Room availability per room type for specified dates.
"""

import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.models.base import AuditMixin


class Hotel(AuditMixin, db.Model):
    """Hotel model representing a partner's property listing.

    Uses AuditMixin for id, created_at, updated_at, and deleted_at (soft delete).

    Attributes:
        partner_user_id: FK to the hotel partner's user account.
        name: Hotel name (max 255 chars).
        address: Full address text.
        destination_id: FK to the destination where the hotel is located.
        star_rating: Integer rating from 1 to 5.
        amenities: JSONB list of amenities (optional).
        contact_email: Contact email (optional).
        contact_phone: Contact phone (optional).
        description: Hotel description (optional).
        is_active: Whether the hotel listing is active.
    """

    __tablename__ = "hotels"

    partner_user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    destination_id = db.Column(
        db.String(36),
        db.ForeignKey("destinations.id"),
        nullable=False,
        index=True,
    )
    star_rating = db.Column(db.Integer, nullable=False)
    amenities = db.Column(db.JSON, nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    room_types = db.relationship(
        "RoomType",
        backref="hotel",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Hotel {self.name}>"


class RoomType(db.Model):
    """Room type model for a hotel.

    Attributes:
        hotel_id: FK to the parent Hotel.
        name: Room type name (e.g., Deluxe, Suite).
        capacity: Maximum number of guests.
        base_price: Base price per night.
        description: Optional description.
        amenities: JSONB list of room amenities (optional).
    """

    __tablename__ = "room_types"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    hotel_id = db.Column(
        db.String(36),
        db.ForeignKey("hotels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    amenities = db.Column(db.JSON, nullable=True)
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
    availability = db.relationship(
        "RoomAvailability",
        backref="room_type",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<RoomType {self.name} (Hotel {self.hotel_id})>"


class RoomAvailability(db.Model):
    """Room availability model tracking available rooms per date.

    Attributes:
        room_type_id: FK to the RoomType.
        date: The date for which availability is recorded.
        available_count: Number of available rooms for that date.
    """

    __tablename__ = "room_availability"
    __table_args__ = (
        db.UniqueConstraint(
            "room_type_id", "date", name="uq_room_availability_type_date"
        ),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    room_type_id = db.Column(
        db.String(36),
        db.ForeignKey("room_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = db.Column(db.Date, nullable=False)
    available_count = db.Column(db.Integer, nullable=False)
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

    def __repr__(self):
        return f"<RoomAvailability {self.room_type_id} on {self.date}: {self.available_count}>"
