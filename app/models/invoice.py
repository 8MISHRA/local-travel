"""Invoice model.

Validates: Requirements 12.1, 12.3
- 12.1: Invoice generation with unique invoice numbers for bookings.
- 12.3: Invoice contains itemized breakdown with subtotal, tax, discount, and total.
"""

from datetime import datetime, timezone

from app.extensions import db
from app.models.base import AuditMixin


class Invoice(AuditMixin, db.Model):
    """Invoice model for booking billing records.

    Attributes:
        invoice_number: Unique invoice identifier (max 20 chars).
        booking_id: FK to the associated booking.
        customer_id: FK to the customer (user) who is billed.
        items: JSONB array of line items with descriptions and amounts.
        subtotal: Sum of item amounts before tax and discounts.
        tax_amount: Tax applied to the invoice.
        discount_amount: Discount applied, defaults to 0.00.
        total_amount: Final amount after tax and discounts.
        issued_at: Timestamp when the invoice was issued.
    """

    __tablename__ = "invoices"

    invoice_number = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )
    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    items = db.Column(db.JSON, nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    issued_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Invoice {self.invoice_number}>"
