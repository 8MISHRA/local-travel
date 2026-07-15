"""Destination and SubDestination models.

Validates: Requirements 6.1, 6.2
- 6.1: Platform supports two primary destinations (Varanasi, Mirzapur)
       with configurable sub-destinations (ghats, temples, waterfalls, hidden places).
- 6.2: Sub-destinations are associated with a parent destination and store
       name, description, location coordinates, category, and media references.
"""

import enum

from app.extensions import db
from app.models.base import AuditMixin


class SubDestinationCategory(enum.Enum):
    """Enumeration of sub-destination categories."""

    ghat = "ghat"
    temple = "temple"
    waterfall = "waterfall"
    hidden_place = "hidden_place"
    market = "market"
    food_spot = "food_spot"
    cultural_site = "cultural_site"


class Destination(AuditMixin, db.Model):
    """Primary destination model (e.g., Varanasi, Mirzapur).

    Attributes:
        name: Unique destination name (max 100 chars).
        description: Optional text description.
        is_primary: Flag indicating a primary destination (Varanasi/Mirzapur).
        sub_destinations: Relationship to associated SubDestination records.
    """

    __tablename__ = "destinations"

    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)

    sub_destinations = db.relationship(
        "SubDestination",
        backref="destination",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Destination {self.name}>"


class SubDestination(AuditMixin, db.Model):
    """Sub-destination within a primary destination.

    Attributes:
        destination_id: FK to parent Destination.
        name: Sub-destination name (max 150 chars).
        description: Optional text description.
        latitude: Geographic latitude (precision 10,8).
        longitude: Geographic longitude (precision 11,8).
        category: Category enum value.
        media_urls: JSONB array of media references.
    """

    __tablename__ = "sub_destinations"

    destination_id = db.Column(
        db.String(36),
        db.ForeignKey("destinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    category = db.Column(
        db.Enum(SubDestinationCategory, name="sub_destination_category"),
        nullable=False,
        index=True,
    )
    media_urls = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<SubDestination {self.name} ({self.category.value})>"
