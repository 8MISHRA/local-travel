"""Scout and ScoutAvailability models.

Validates: Requirements 9.1
- 9.1: Local scouts are assigned to bookings based on operating area,
       availability, language, and specialization.
"""

import enum
import uuid

from app.extensions import db
from app.models.base import AuditMixin


class OperatingArea(enum.Enum):
    """Enumeration of supported operating areas for scouts and drivers."""

    varanasi = "varanasi"
    mirzapur = "mirzapur"


class Scout(AuditMixin, db.Model):
    """Scout model representing a local guide.

    Attributes:
        user_id: FK to the associated user account (unique, one scout per user).
        languages: JSONB list of languages the scout speaks.
        specializations: JSONB list of specialization areas (optional).
        operating_area: The geographic area the scout operates in.
        is_available: Whether the scout is currently available for assignments.
        average_rating: Average rating from traveller reviews.
        total_assignments: Count of completed assignments.
    """

    __tablename__ = "scouts"

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    languages = db.Column(db.JSON, nullable=False)
    specializations = db.Column(db.JSON, nullable=True)
    operating_area = db.Column(
        db.Enum(OperatingArea, name="operating_area_enum"),
        nullable=False,
        index=True,
    )
    is_available = db.Column(db.Boolean, default=True, nullable=False, index=True)
    average_rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_assignments = db.Column(db.Integer, default=0)

    # Relationships
    availabilities = db.relationship(
        "ScoutAvailability",
        backref="scout",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Scout user_id={self.user_id} area={self.operating_area.value}>"


class ScoutAvailability(db.Model):
    """Date-specific availability record for a scout.

    Attributes:
        scout_id: FK to the parent Scout.
        date: The date this availability record applies to.
        is_available: Whether the scout is available on this date.
    """

    __tablename__ = "scout_availabilities"
    __table_args__ = (
        db.UniqueConstraint("scout_id", "date", name="uq_scout_availability_date"),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    scout_id = db.Column(
        db.String(36),
        db.ForeignKey("scouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = db.Column(db.Date, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<ScoutAvailability scout_id={self.scout_id} date={self.date}>"
