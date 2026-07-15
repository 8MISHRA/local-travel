"""EnterpriseBooking model for group/corporate travel inquiries.

Validates: Requirement 16.1
- 16.1: Enterprise/group booking request form with company details,
  group size (5-500), travel dates, budget range, and quotation workflow.
"""

import enum
from datetime import datetime, timezone

from app.extensions import db
from app.models.base import AuditMixin


class EnterpriseBookingStatus(enum.Enum):
    """Enumeration of enterprise booking lifecycle statuses."""

    pending_review = "pending_review"
    quotation_sent = "quotation_sent"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class EnterpriseBooking(AuditMixin, db.Model):
    """Enterprise booking model for corporate/group travel requests.

    Supports the full enterprise booking workflow from initial inquiry
    through quotation, confirmation, and completion.
    """

    __tablename__ = "enterprise_bookings"

    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    company_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(150), nullable=False)
    contact_email = db.Column(db.String(255), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    group_size = db.Column(db.Integer, nullable=False)
    travel_start_date = db.Column(db.Date, nullable=False)
    travel_end_date = db.Column(db.Date, nullable=False)
    destination_id = db.Column(
        db.String(36),
        db.ForeignKey("destinations.id"),
        nullable=False,
    )
    special_requirements = db.Column(db.Text, nullable=True)
    budget_min = db.Column(db.Numeric(12, 2), nullable=True)
    budget_max = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(
        db.Enum(EnterpriseBookingStatus, name="enterprise_booking_status_enum"),
        nullable=False,
        default=EnterpriseBookingStatus.pending_review,
    )
    quotation = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f"<EnterpriseBooking {self.company_name} ({self.status.value})>"
