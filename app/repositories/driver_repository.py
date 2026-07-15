"""Driver repository for data access operations on drivers and availability.

Validates: Requirements 10.1, 10.2, 10.4
- 10.1: Driver CRUD with operating area, vehicle details, availability
- 10.2: Assign driver to booking, update availability
- 10.4: Conflict detection for overlapping date ranges
"""

import math
from datetime import timedelta

from sqlalchemy import and_

from app.models.booking import BookingDriver
from app.models.driver import Driver, DriverAvailability
from app.repositories.base_repository import BaseRepository


class DriverRepository(BaseRepository):
    """Repository for Driver model with availability and conflict detection."""

    model_class = Driver

    def list_drivers(self, page=1, per_page=20, filters=None, sort_by=None):
        """Return paginated list of non-deleted drivers.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (max 100).
            filters: Dict of equality filters (operating_area, is_available, etc.)
            sort_by: Sort field string.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        query = self.session.query(Driver).filter(
            Driver.deleted_at.is_(None),
        )

        if filters:
            query = self._apply_filters(query, filters)

        if sort_by:
            query = self._apply_sorting(query, sort_by)
        else:
            query = query.order_by(Driver.created_at.desc())

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

    def check_conflicts(self, driver_id, start_date, end_date):
        """Check if a driver has overlapping assignments for a date range.

        Looks at DriverAvailability records marked as unavailable (is_available=False)
        within the specified date range, indicating existing assignments.

        Args:
            driver_id: UUID of the driver.
            start_date: Start date of the booking (inclusive).
            end_date: End date of the booking (inclusive).

        Returns:
            List of conflicting dates (as date objects) where the driver is unavailable.
        """
        conflicting = (
            self.session.query(DriverAvailability)
            .filter(
                DriverAvailability.driver_id == driver_id,
                DriverAvailability.date >= start_date,
                DriverAvailability.date <= end_date,
                DriverAvailability.is_available.is_(False),
            )
            .all()
        )
        return [record.date for record in conflicting]

    def update_availability(self, driver_id, start_date, end_date, is_available=False):
        """Set driver availability for a date range.

        Creates or updates DriverAvailability records for each date in
        [start_date, end_date] inclusive.

        Args:
            driver_id: UUID of the driver.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            is_available: Whether the driver is available (default False for assignments).

        Returns:
            List of created/updated DriverAvailability records.
        """
        results = []
        current_date = start_date
        while current_date <= end_date:
            existing = (
                self.session.query(DriverAvailability)
                .filter(
                    DriverAvailability.driver_id == driver_id,
                    DriverAvailability.date == current_date,
                )
                .first()
            )

            if existing:
                existing.is_available = is_available
                results.append(existing)
            else:
                availability = DriverAvailability(
                    driver_id=driver_id,
                    date=current_date,
                    is_available=is_available,
                )
                self.session.add(availability)
                results.append(availability)

            current_date += timedelta(days=1)

        self.session.flush()
        return results

    def create_booking_driver(self, booking_id, driver_id, assigned_by):
        """Create a BookingDriver assignment record.

        Args:
            booking_id: UUID of the booking.
            driver_id: UUID of the driver.
            assigned_by: UUID of the admin user making the assignment.

        Returns:
            The created BookingDriver instance.
        """
        booking_driver = BookingDriver(
            booking_id=booking_id,
            driver_id=driver_id,
            assigned_by=assigned_by,
        )
        self.session.add(booking_driver)
        self.session.flush()
        return booking_driver

    def get_driver_by_user_id(self, user_id):
        """Get a driver by their associated user ID.

        Args:
            user_id: UUID of the user.

        Returns:
            Driver instance or None.
        """
        return (
            self.session.query(Driver)
            .filter(
                Driver.user_id == user_id,
                Driver.deleted_at.is_(None),
            )
            .first()
        )
