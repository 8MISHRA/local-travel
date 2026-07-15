"""Booking repository for data access operations on bookings and status history.

Validates: Requirements 7.1, 7.2, 7.4, 7.6, 7.7
- 7.1: Create booking records with package, travel dates, travellers
- 7.2: Update booking with hotel, transport, add-ons and calculate price
- 7.4: Track booking status lifecycle
- 7.6: Status change recording with timestamp and acting user
- 7.7: Customer-scoped listing with pagination and status filtering
"""

import math
import random
import string
from datetime import datetime, timezone

from app.models.booking import Booking, BookingStatus, BookingStatusHistory
from app.repositories.base_repository import BaseRepository


class BookingRepository(BaseRepository):
    """Repository for Booking model with customer-scoped queries and booking number generation."""

    model_class = Booking

    def list_for_customer(self, customer_id, page=1, per_page=20, status_filter=None):
        """Return paginated bookings for a specific customer or all bookings.

        Only returns non-deleted bookings. If customer_id is provided, filters
        to only that customer's bookings. If None, returns all bookings (admin use).
        Optionally filters by booking status.

        Args:
            customer_id: UUID of the customer, or None for all bookings.
            page: Page number (1-indexed).
            per_page: Items per page (max 100).
            status_filter: Optional BookingStatus enum value to filter by.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        query = self.session.query(Booking).filter(
            Booking.deleted_at.is_(None),
        )

        if customer_id is not None:
            query = query.filter(Booking.customer_id == customer_id)

        if status_filter is not None:
            query = query.filter(Booking.status == status_filter)

        query = query.order_by(Booking.created_at.desc())

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

    def generate_booking_number(self):
        """Generate a unique booking number in format BK-YYYYMMDD-XXXXX.

        The XXXXX portion is a random 5-character uppercase alphanumeric string.
        Retries up to 10 times to ensure uniqueness.

        Returns:
            A unique booking number string.

        Raises:
            RuntimeError: If a unique number cannot be generated after 10 attempts.
        """
        for _ in range(10):
            date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
            random_part = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=5)
            )
            booking_number = f"BK-{date_part}-{random_part}"

            existing = self.session.query(Booking).filter(
                Booking.booking_number == booking_number
            ).first()
            if existing is None:
                return booking_number

        raise RuntimeError("Unable to generate a unique booking number after 10 attempts.")

    def create_status_history(self, booking_id, from_status, to_status, changed_by, notes=None):
        """Create a booking status history record.

        Args:
            booking_id: UUID of the booking.
            from_status: Previous status value (string or None for initial creation).
            to_status: New status value (string).
            changed_by: UUID of the user who made the change.
            notes: Optional notes about the status change.

        Returns:
            The created BookingStatusHistory instance.
        """
        history = BookingStatusHistory(
            booking_id=booking_id,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            notes=notes,
        )
        self.session.add(history)
        self.session.flush()
        return history
