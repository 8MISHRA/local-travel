"""Coupon model for discount code management.

Validates: Requirement 17.1
- 17.1: Coupon system with percentage/fixed discount types, validity dates,
  usage limits, minimum booking amount, and maximum discount cap.
"""

import enum
from datetime import datetime, timezone

from app.extensions import db
from app.models.base import AuditMixin


class DiscountType(enum.Enum):
    """Enumeration of supported discount types."""

    percentage = "percentage"
    fixed = "fixed"


class Coupon(AuditMixin, db.Model):
    """Coupon model for managing promotional discount codes.

    Supports both percentage and fixed-amount discounts with configurable
    validity periods, usage limits, and minimum/maximum constraints.
    """

    __tablename__ = "coupons"

    code = db.Column(
        db.String(50), unique=True, nullable=False, index=True
    )
    discount_type = db.Column(
        db.Enum(DiscountType, name="discount_type_enum"),
        nullable=False,
    )
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    min_booking_amount = db.Column(db.Numeric(12, 2), nullable=True)
    max_discount_cap = db.Column(db.Numeric(12, 2), nullable=True)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    usage_limit = db.Column(db.Integer, nullable=True)
    usage_count = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Coupon {self.code} ({self.discount_type.value})>"
