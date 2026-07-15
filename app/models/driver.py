"""Driver and DriverAvailability models.

Validates: Requirements 10.1
- 10.1: Drivers are assigned to bookings based on operating area,
       vehicle type, and availability.
"""

import uuid

from app.extensions import db
from app.models.base import AuditMixin
from app.models.scout import OperatingArea


class Driver(AuditMixin, db.Model):
    """Driver model representing a local transport provider.

    Attributes:
        user_id: FK to the associated user account (unique, one driver per user).
        vehicle_type: Type of vehicle the driver operates (e.g., car, auto, van).
        vehicle_number: Registration number of the vehicle.
        license_number: Driver's license number.
        operating_area: The geographic area the driver operates in.
        is_available: Whether the driver is currently available for assignments.
        average_rating: Average rating from traveller reviews.
        total_assignments: Count of completed assignments.
    """

    __tablename__ = "drivers"

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    vehicle_type = db.Column(db.String(50), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    operating_area = db.Column(
        db.Enum(OperatingArea, name="operating_area_enum", create_type=False),
        nullable=False,
        index=True,
    )
    is_available = db.Column(db.Boolean, default=True, nullable=False, index=True)
    average_rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_assignments = db.Column(db.Integer, default=0)

    # Relationships
    availabilities = db.relationship(
        "DriverAvailability",
        backref="driver",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Driver user_id={self.user_id} area={self.operating_area.value}>"


class DriverAvailability(db.Model):
    """Date-specific availability record for a driver.

    Attributes:
        driver_id: FK to the parent Driver.
        date: The date this availability record applies to.
        is_available: Whether the driver is available on this date.
    """

    __tablename__ = "driver_availabilities"
    __table_args__ = (
        db.UniqueConstraint("driver_id", "date", name="uq_driver_availability_date"),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    driver_id = db.Column(
        db.String(36),
        db.ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = db.Column(db.Date, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<DriverAvailability driver_id={self.driver_id} date={self.date}>"
