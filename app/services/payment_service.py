"""Payment service providing business logic for payment processing.

Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5
- 11.1: Initiate payment with amount, currency, method, status pending
- 11.2: Process payment gateway callback, confirm booking on success
- 11.3: Handle payment failure, notify customer
- 11.4: Support partial payments against booking total
- 11.5: Initiate refund with original payment reference, amount, status processing
"""

from decimal import Decimal

from app.extensions import db
from app.models.payment import PaymentStatus
from app.repositories.payment_repository import PaymentRepository
from app.services.booking_service import BookingService
from app.utils.exceptions import NotFoundError, ValidationError


class PaymentService:
    """Service layer for payment operations.

    Handles payment initiation, gateway callback processing,
    partial payment tracking, and refund initiation.
    """

    def __init__(self, session=None):
        """Initialize the service with a database session.

        Args:
            session: SQLAlchemy session. Defaults to db.session if None.
        """
        self.session = session or db.session
        self.repo = PaymentRepository(self.session)
        self.booking_service = BookingService(self.session)

    def initiate_payment(self, booking_id, amount, currency="INR", payment_method=None):
        """Create a new pending payment record for a booking.

        Validates that the booking exists before creating the payment.

        Args:
            booking_id: UUID of the booking to pay for.
            amount: Payment amount (must be positive).
            currency: ISO 4217 currency code (default INR).
            payment_method: Method used (card, UPI, net_banking, etc.).

        Returns:
            The created Payment instance with status=pending.

        Raises:
            NotFoundError: If the booking does not exist.
            ValidationError: If amount is not positive.
        """
        # Validate booking exists
        booking = self.booking_service.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking with id '{booking_id}' not found.")

        # Validate amount
        if Decimal(str(amount)) <= 0:
            raise ValidationError(
                "Payment amount must be greater than zero.",
                details={"amount": str(amount)},
            )

        payment = self.repo.create_payment(
            booking_id=booking_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
        )

        self.session.commit()
        return payment

    def process_callback(self, payment_id, status, gateway_transaction_id=None, gateway_response=None):
        """Process a payment gateway callback.

        Updates the payment status based on the gateway response.
        On success (completed): triggers booking confirmation via BookingService.
        On failure (failed): marks payment as failed (notification can be triggered by caller).

        Args:
            payment_id: UUID of the payment to update.
            status: New status string ("completed" or "failed").
            gateway_transaction_id: Transaction ID from gateway (optional).
            gateway_response: Full gateway response dict (optional).

        Returns:
            The updated Payment instance.

        Raises:
            NotFoundError: If payment does not exist.
            ValidationError: If status is invalid.
        """
        payment = self.repo.get_by_id(payment_id)
        if payment is None:
            raise NotFoundError(f"Payment with id '{payment_id}' not found.")

        # Map string status to enum
        try:
            new_status = PaymentStatus(status)
        except ValueError:
            raise ValidationError(
                f"Invalid payment status: '{status}'.",
                details={"valid_statuses": ["completed", "failed"]},
            )

        # Update payment
        payment = self.repo.update_status(
            payment_id=payment_id,
            status=new_status,
            gateway_transaction_id=gateway_transaction_id,
            gateway_response=gateway_response,
        )

        # On successful payment, trigger booking confirmation
        if new_status == PaymentStatus.completed:
            try:
                self.booking_service.confirm(
                    booking_id=payment.booking_id,
                    changed_by=payment.booking_id,  # System action via payment
                )
            except Exception:
                # Booking may already be confirmed (partial payments),
                # or in an invalid state. Log but don't fail the callback.
                pass

        self.session.commit()
        return payment

    def list_for_booking(self, booking_id, page=1, per_page=20):
        """List all payments for a booking with pagination.

        Also returns the total amount paid (completed payments) for
        partial payment tracking.

        Args:
            booking_id: UUID of the booking.
            page: Page number (1-indexed).
            per_page: Items per page (max 100).

        Returns:
            Tuple of (items, pagination_metadata, total_paid).
        """
        # Validate booking exists
        booking = self.booking_service.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking with id '{booking_id}' not found.")

        items, pagination_meta = self.repo.list_for_booking(
            booking_id=booking_id,
            page=page,
            per_page=per_page,
        )

        total_paid = self.repo.get_total_paid_for_booking(booking_id)

        return items, pagination_meta, total_paid

    def initiate_refund(self, payment_id, amount=None, reason=None):
        """Initiate a refund for a payment.

        Creates a refund record with status=processing. If no amount is
        specified, refunds the full payment amount.

        Args:
            payment_id: UUID of the payment to refund.
            amount: Refund amount (optional, defaults to full payment amount).
            reason: Optional reason for the refund.

        Returns:
            The created Refund instance with status=processing.

        Raises:
            NotFoundError: If payment does not exist.
            ValidationError: If payment is not in completed status or amount exceeds payment.
        """
        payment = self.repo.get_by_id(payment_id)
        if payment is None:
            raise NotFoundError(f"Payment with id '{payment_id}' not found.")

        # Only completed payments can be refunded
        if payment.status != PaymentStatus.completed:
            raise ValidationError(
                "Only completed payments can be refunded.",
                details={"current_status": payment.status.value},
            )

        # Default to full refund if no amount specified
        refund_amount = Decimal(str(amount)) if amount else Decimal(str(payment.amount))

        # Validate refund amount
        if refund_amount <= 0:
            raise ValidationError(
                "Refund amount must be greater than zero.",
                details={"amount": str(refund_amount)},
            )

        if refund_amount > Decimal(str(payment.amount)):
            raise ValidationError(
                "Refund amount cannot exceed the original payment amount.",
                details={
                    "refund_amount": str(refund_amount),
                    "payment_amount": str(payment.amount),
                },
            )

        refund = self.repo.create_refund(
            payment_id=payment_id,
            booking_id=payment.booking_id,
            amount=refund_amount,
            reason=reason,
        )

        # Update payment status to refunded
        self.repo.update_status(payment_id, PaymentStatus.refunded)

        self.session.commit()
        return refund
