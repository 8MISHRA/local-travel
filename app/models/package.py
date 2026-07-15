"""Package, PricingTier, and Itinerary models.

Validates: Requirements 5.1, 5.5, 5.6
- 5.1: Curated travel packages with duration, traveller type, inclusions/exclusions
- 5.5: Package pricing with tiered options
- 5.6: Day-wise itinerary for each package
"""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db
from app.models.base import AuditMixin


class TravellerType(enum.Enum):
    """Enum representing supported traveller types for packages."""

    solo = "solo"
    couple = "couple"
    family = "family"
    group = "group"
    corporate = "corporate"


class Package(AuditMixin, db.Model):
    """Travel package model.

    Represents a curated travel experience with duration, traveller type,
    inclusions/exclusions, and associated pricing tiers and itineraries.
    """

    __tablename__ = "packages"

    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    destination_id = db.Column(
        db.String(36),
        db.ForeignKey("destinations.id"),
        nullable=False,
        index=True,
    )
    duration_days = db.Column(db.Integer, nullable=False)
    duration_nights = db.Column(db.Integer, nullable=False)
    traveller_type = db.Column(
        db.Enum(TravellerType, name="traveller_type_enum"),
        nullable=False,
        index=True,
    )
    inclusions = db.Column(db.JSON, nullable=False)
    exclusions = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    featured_image_url = db.Column(db.String(500), nullable=True)
    average_rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_reviews = db.Column(db.Integer, default=0)

    # Relationships
    pricing_tiers = db.relationship(
        "PricingTier",
        backref="package",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    itineraries = db.relationship(
        "Itinerary",
        backref="package",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Package {self.title}>"


class PricingTier(db.Model):
    """Pricing tier model for packages.

    Each package can have multiple pricing tiers (e.g., budget, standard, premium).
    """

    __tablename__ = "pricing_tiers"
    __table_args__ = (
        db.UniqueConstraint("package_id", "tier_name", name="uq_pricing_tier_package_tier"),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    package_id = db.Column(
        db.String(36),
        db.ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    max_persons = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<PricingTier {self.tier_name} for Package {self.package_id}>"


class Itinerary(db.Model):
    """Day-wise itinerary model for packages.

    Each package has a sequence of days with activities and descriptions.
    """

    __tablename__ = "itineraries"
    __table_args__ = (
        db.UniqueConstraint("package_id", "day_number", name="uq_itinerary_package_day"),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    package_id = db.Column(
        db.String(36),
        db.ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    activities = db.Column(db.JSON, nullable=False)

    def __repr__(self):
        return f"<Itinerary Day {self.day_number} for Package {self.package_id}>"
