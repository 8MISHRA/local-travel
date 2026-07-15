"""Payment and Refund models.

Validates: Requirements 11.1, 11.5
- 11.1: Payment processing with multiple payment methods and gateway integration.
- 11.5: Refund processing with status tracking and reason documentation.
"""

import enum

from app.extensions import db
from app.models.base import AuditMixin


class PaymentStatus(enum.Enum):
    """Enumeration of payment statuses."""

    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class RefundStatus(enum.Enum):
    """Enumeration of refund statuses."""

    processing = "processing"
    completed = "completed"
    failed = "failed"


class Payment(AuditMixin, db.Model):
    """Payment model tracking transactions for bookings.

    Attributes:
        booking_id: FK to the associated booking.
        amount: Payment amount with precision (12,2).
        currency: ISO 4217 currency code, defaults to 'INR'.
        payment_method: Method used (e.g., card, UPI, net_banking).
        gateway_transaction_id: Unique transaction ID from payment gateway.
        status: Current payment status enum.
        gateway_response: Full gateway response stored as JSONB.
    """

    __tablename__ = "payments"

    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="INR")
    payment_method = db.Column(db.String(50), nullable=True)
    gateway_transaction_id = db.Column(db.String(255), nullable=True, index=True)
    status = db.Column(
        db.Enum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.pending,
        index=True,
    )
    gateway_response = db.Column(db.JSON, nullable=True)

    # Relationships
    refunds = db.relationship(
        "Refund",
        backref="payment",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Payment {self.id} status={self.status.value}>"


class Refund(AuditMixin, db.Model):
    """Refund model tracking refund requests against payments.

    Attributes:
        payment_id: FK to the original payment.
        booking_id: FK to the associated booking.
        amount: Refund amount with precision (12,2).
        reason: Optional text explaining the refund reason.
        status: Current refund processing status.
    """

    __tablename__ = "refunds"

    payment_id = db.Column(
        db.String(36),
        db.ForeignKey("payments.id"),
        nullable=False,
        index=True,
    )
    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(RefundStatus, name="refund_status_enum"),
        nullable=False,
        default=RefundStatus.processing,
        index=True,
    )

    def __repr__(self):
        return f"<Refund {self.id} status={self.status.value}>"
