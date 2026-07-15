"""Booking service providing business logic for booking management.

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
- 7.1: Create draft booking with package, dates, travellers
- 7.2: Submit details (hotel, transport, add-ons), calculate price, transition to pending_payment
- 7.3: Confirm booking (payment received), transition to confirmed
- 7.4: Full booking status lifecycle (draft → pending_payment → confirmed → in_progress → completed/cancelled/refunded)
- 7.5: Cancel confirmed booking, initiate refund
- 7.6: Record status changes with timestamp and acting user
- 7.7: Customer-scoped listing with pagination and status filtering
"""

from decimal import Decimal

from app.extensions import db
from app.models.booking import Booking, BookingStatus
from app.models.package import PricingTier
from app.repositories.booking_repository import BookingRepository
from app.utils.exceptions import InvalidStateTransitionError, NotFoundError


class BookingStateMachine:
    """Manages valid booking status transitions.

    Enforces the booking lifecycle by defining which status transitions
    are permitted and recording each transition in the status history.
    """

    TRANSITIONS = {
        BookingStatus.draft: [BookingStatus.pending_payment],
        BookingStatus.pending_payment: [BookingStatus.confirmed, BookingStatus.cancelled],
        BookingStatus.confirmed: [BookingStatus.in_progress, BookingStatus.cancelled],
        BookingStatus.in_progress: [BookingStatus.completed],
        BookingStatus.cancelled: [BookingStatus.refunded],
        BookingStatus.completed: [],
        BookingStatus.refunded: [],
    }

    def can_transition(self, current_status, target_status):
        """Check if a transition from current_status to target_status is valid.

        Args:
            current_status: The current BookingStatus.
            target_status: The desired BookingStatus.

        Returns:
            True if the transition is allowed, False otherwise.
        """
        allowed = self.TRANSITIONS.get(current_status, [])
        return target_status in allowed

    def transition(self, booking, target_status, changed_by, repo, notes=None):
        """Execute a status transition on a booking.

        Updates the booking status and creates a BookingStatusHistory record.

        Args:
            booking: The Booking instance to transition.
            target_status: The desired BookingStatus.
            changed_by: UUID of the user performing the transition.
            repo: BookingRepository instance for creating history records.
            notes: Optional notes about the transition.

        Returns:
            The updated Booking instance.

        Raises:
            InvalidStateTransitionError: If the transition is not allowed.
        """
        if not self.can_transition(booking.status, target_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from '{booking.status.value}' to '{target_status.value}'.",
                details={
                    "current_status": booking.status.value,
                    "target_status": target_status.value,
                    "allowed_transitions": [
                        s.value for s in self.TRANSITIONS.get(booking.status, [])
                    ],
                },
            )

        from_status = booking.status.value
        booking.status = target_status

        repo.create_status_history(
            booking_id=booking.id,
            from_status=from_status,
            to_status=target_status.value,
            changed_by=changed_by,
            notes=notes,
        )

        return booking


class BookingService:
    """Service layer for booking management operations.

    Handles the full booking lifecycle: creation, detail submission,
    confirmation, cancellation, status updates, and customer listing.
    """

    def __init__(self, session=None):
        """Initialize the service with a database session.

        Args:
            session: SQLAlchemy session. Defaults to db.session if None.
        """
        self.session = session or db.session
        self.repo = BookingRepository(self.session)
        self.state_machine = BookingStateMachine()

    def create_draft(
        self,
        customer_id,
        package_id,
        travel_start_date,
        travel_end_date,
        num_travellers,
        traveller_type,
    ):
        """Create a new draft booking.

        Generates a unique booking number and creates the booking in draft status.

        Args:
            customer_id: UUID of the customer creating the booking.
            package_id: UUID of the selected package.
            travel_start_date: Start date for travel.
            travel_end_date: End date for travel.
            num_travellers: Number of travellers.
            traveller_type: Type of traveller (solo, couple, family, group, corporate).

        Returns:
            The created Booking instance.
        """
        booking_number = self.repo.generate_booking_number()

        booking = self.repo.create(
            booking_number=booking_number,
            customer_id=customer_id,
            package_id=package_id,
            status=BookingStatus.draft,
            travel_start_date=travel_start_date,
            travel_end_date=travel_end_date,
            num_travellers=num_travellers,
            traveller_type=traveller_type,
        )

        # Record initial status in history
        self.repo.create_status_history(
            booking_id=booking.id,
            from_status=None,
            to_status=BookingStatus.draft.value,
            changed_by=customer_id,
            notes="Booking created as draft.",
        )

        self.session.commit()
        return booking

    def submit_details(
        self,
        booking_id,
        hotel_preference_id=None,
        room_type_id=None,
        transport_preferences=None,
        add_ons=None,
        changed_by=None,
    ):
        """Submit booking details and transition to pending_payment.

        Updates the booking with hotel, transport, and add-on preferences,
        calculates the total price, and transitions status to pending_payment.

        Args:
            booking_id: UUID of the booking to update.
            hotel_preference_id: UUID of the selected hotel (optional).
            room_type_id: UUID of the selected room type (optional).
            transport_preferences: Dict of transport preferences (optional).
            add_ons: List of add-on selections (optional).
            changed_by: UUID of the user submitting details.

        Returns:
            The updated Booking instance.

        Raises:
            NotFoundError: If booking does not exist or is deleted.
            InvalidStateTransitionError: If booking is not in draft status.
        """
        booking = self.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking with id '{booking_id}' not found.")

        # Update booking details
        booking.hotel_preference_id = hotel_preference_id
        booking.room_type_id = room_type_id
        booking.transport_preferences = transport_preferences
        booking.add_ons = add_ons

        # Calculate price
        self._calculate_price(booking)

        # Determine who is making the change
        actor = changed_by or booking.customer_id

        # Transition to pending_payment
        self.state_machine.transition(
            booking=booking,
            target_status=BookingStatus.pending_payment,
            changed_by=actor,
            repo=self.repo,
            notes="Booking details submitted, awaiting payment.",
        )

        self.session.commit()
        return booking

    def confirm(self, booking_id, changed_by):
        """Confirm a booking after payment is received.

        Transitions the booking from pending_payment to confirmed.

        Args:
            booking_id: UUID of the booking to confirm.
            changed_by: UUID of the user/system confirming the booking.

        Returns:
            The updated Booking instance.

        Raises:
            NotFoundError: If booking does not exist or is deleted.
            InvalidStateTransitionError: If booking is not in pending_payment status.
        """
        booking = self.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking with id '{booking_id}' not found.")

        self.state_machine.transition(
            booking=booking,
            target_status=BookingStatus.confirmed,
            changed_by=changed_by,
            repo=self.repo,
            notes="Payment confirmed.",
        )

        self.session.commit()
        return booking

    def cancel(self, booking_id, changed_by, notes=None):
        """Cancel a booking and initiate refund process if applicable.

        Transitions the booking to cancelled. If the booking was in
        confirmed status, a refund should be initiated by the caller.

        Args:
            booking_id: UUID of the booking to cancel.
            changed_by: UUID of the user requesting cancellation.
            notes: Optional reason for cancellation.

        Returns:
            Tuple of (booking, initiate_refund) where initiate_refund is True
            if the booking was confirmed (refund should be processed).

        Raises:
            NotFoundError: If booking does not exist or is deleted.
            InvalidStateTransitionError: If booking cannot be cancelled from current status.
        """
        booking = self.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking with id '{booking_id}' not found.")

        # Determine if refund should be initiated (cancelling a confirmed booking)
        initiate_refund = booking.status == BookingStatus.confirmed

        self.state_machine.transition(
            booking=booking,
            target_status=BookingStatus.cancelled,
            changed_by=changed_by,
            repo=self.repo,
            notes=notes or "Booking cancelled by customer.",
        )

        self.session.commit()
        return booking, initiate_refund

    def update_status(self, booking_id, target_status, changed_by, notes=None):
        """Update a booking's status to any valid next status.

        General-purpose status transition method for admin/scout use.

        Args:
            booking_id: UUID of the booking.
            target_status: The desired BookingStatus enum value.
            changed_by: UUID of the user performing the update.
            notes: Optional notes about the status change.

        Returns:
            The updated Booking instance.

        Raises:
            NotFoundError: If booking does not exist or is deleted.
            InvalidStateTransitionError: If the transition is not allowed.
        """
        booking = self.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(f"Booking with id '{booking_id}' not found.")

        self.state_machine.transition(
            booking=booking,
            target_status=target_status,
            changed_by=changed_by,
            repo=self.repo,
            notes=notes,
        )

        self.session.commit()
        return booking

    def list_for_customer(self, customer_id, page=1, per_page=20, status=None):
        """List bookings for a specific customer with pagination and filtering.

        Args:
            customer_id: UUID of the customer.
            page: Page number (1-indexed).
            per_page: Items per page (max 100).
            status: Optional BookingStatus enum value to filter by.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        return self.repo.list_for_customer(
            customer_id=customer_id,
            page=page,
            per_page=per_page,
            status_filter=status,
        )

    def _calculate_price(self, booking):
        """Calculate the total price for a booking based on the package pricing tier.

        Looks up the pricing tier matching the booking's traveller_type.
        Falls back to the first available tier if no exact match is found.
        Applies a simple calculation: tier_price * num_travellers.
        Tax is calculated at 18% (GST).

        Args:
            booking: The Booking instance to calculate pricing for.
        """
        # Find the matching pricing tier for this package and traveller type
        tier = self.session.query(PricingTier).filter(
            PricingTier.package_id == booking.package_id,
            PricingTier.tier_name == booking.traveller_type,
        ).first()

        # Fallback to first available tier if no match
        if tier is None:
            tier = self.session.query(PricingTier).filter(
                PricingTier.package_id == booking.package_id,
            ).first()

        if tier is not None:
            base_price = Decimal(str(tier.price))
            num_travellers = booking.num_travellers

            subtotal = base_price * num_travellers
            tax_rate = Decimal("0.18")  # 18% GST
            tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"))
            total_amount = subtotal + tax_amount

            booking.subtotal = subtotal
            booking.tax_amount = tax_amount
            booking.total_amount = total_amount
        else:
            # No pricing tier found; leave amounts as None
            booking.subtotal = None
            booking.tax_amount = None
            booking.total_amount = None
