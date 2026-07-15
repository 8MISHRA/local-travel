"""Payment repository for data access operations on payments and refunds.

Validates: Requirements 11.1, 11.4, 11.5
- 11.1: Payment record creation with amount, currency, method, and pending status
- 11.4: Partial payment tracking, listing all payments for a booking
- 11.5: Refund record creation with status tracking
"""

import math
from decimal import Decimal

from app.models.payment import Payment, PaymentStatus, Refund, RefundStatus
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository):
    """Repository for Payment model with booking-scoped queries and partial payment tracking."""

    model_class = Payment

    def list_for_booking(self, booking_id, page=1, per_page=20):
        """Return paginated payments for a specific booking.

        Args:
            booking_id: UUID of the booking.
            page: Page number (1-indexed).
            per_page: Items per page (max 100).

        Returns:
            Tuple of (items, pagination_metadata).
        """
        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        query = self.session.query(Payment).filter(
            Payment.booking_id == booking_id,
        ).order_by(Payment.created_at.desc())

        total = query.count()
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        pagination_meta = {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

        return items, pagination_meta

    def get_total_paid_for_booking(self, booking_id):
        """Calculate total amount paid (completed payments) for a booking.

        Used for partial payment tracking to determine remaining balance.

        Args:
            booking_id: UUID of the booking.

        Returns:
            Decimal total of all completed payments for the booking.
        """
        payments = self.session.query(Payment).filter(
            Payment.booking_id == booking_id,
            Payment.status == PaymentStatus.completed,
        ).all()

        total = sum(
            (Decimal(str(p.amount)) for p in payments),
            Decimal("0.00"),
        )
        return total

    def get_by_id(self, payment_id):
        """Fetch a single payment by its primary key.

        Payments do not use soft delete, so we simply look up by id.

        Args:
            payment_id: UUID of the payment.

        Returns:
            Payment instance or None.
        """
        return self.session.query(Payment).filter(
            Payment.id == payment_id,
        ).first()

    def create_payment(self, booking_id, amount, currency="INR", payment_method=None):
        """Create a new payment record with pending status.

        Args:
            booking_id: UUID of the associated booking.
            amount: Payment amount.
            currency: ISO 4217 currency code (default INR).
            payment_method: Payment method (e.g., card, UPI, net_banking).

        Returns:
            The created Payment instance.
        """
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status=PaymentStatus.pending,
        )
        self.session.add(payment)
        self.session.flush()
        return payment

    def update_status(self, payment_id, status, gateway_transaction_id=None, gateway_response=None):
        """Update a payment's status and optional gateway details.

        Args:
            payment_id: UUID of the payment to update.
            status: New PaymentStatus enum value.
            gateway_transaction_id: Transaction ID from gateway (optional).
            gateway_response: Full gateway response dict (optional).

        Returns:
            Updated Payment instance or None if not found.
        """
        payment = self.get_by_id(payment_id)
        if payment is None:
            return None

        payment.status = status
        if gateway_transaction_id is not None:
            payment.gateway_transaction_id = gateway_transaction_id
        if gateway_response is not None:
            payment.gateway_response = gateway_response

        self.session.flush()
        return payment

    def create_refund(self, payment_id, booking_id, amount, reason=None):
        """Create a new refund record with processing status.

        Args:
            payment_id: UUID of the original payment.
            booking_id: UUID of the associated booking.
            amount: Refund amount.
            reason: Optional reason for the refund.

        Returns:
            The created Refund instance.
        """
        refund = Refund(
            payment_id=payment_id,
            booking_id=booking_id,
            amount=amount,
            reason=reason,
            status=RefundStatus.processing,
        )
        self.session.add(refund)
        self.session.flush()
        return refund
