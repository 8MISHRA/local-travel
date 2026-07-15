"""Driver service with business logic for driver management and booking assignment.

Validates: Requirements 10.1, 10.2, 10.3, 10.4
- 10.1: Create driver profile with name, phone, vehicle type, vehicle number,
         license details, operating area, availability
- 10.2: Assign driver to booking, update availability for booking dates
- 10.3: Store driver rating (1-5) and update average_rating
- 10.4: Reject assignment if driver has overlapping assignment (HTTP 409)
"""

from decimal import Decimal

from flask import g

from app.extensions import db
from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository
from app.repositories.driver_repository import DriverRepository
from app.utils.exceptions import ConflictError, NotFoundError, ValidationError


class DriverService:
    """Service layer for driver management operations."""

    def __init__(self):
        self.driver_repo = DriverRepository(db.session)
        self.booking_repo = BookingRepository(db.session)

    def create_driver(
        self,
        user_id,
        vehicle_type,
        vehicle_number,
        license_number,
        operating_area,
    ):
        """Create a new driver profile.

        Args:
            user_id: UUID of the user account for this driver.
            vehicle_type: Type of vehicle (car, auto, van, etc.).
            vehicle_number: Vehicle registration number.
            license_number: Driver's license number.
            operating_area: OperatingArea enum value.

        Returns:
            The created Driver instance.

        Raises:
            ConflictError: If a driver profile already exists for this user.
        """
        existing = self.driver_repo.get_driver_by_user_id(user_id)
        if existing:
            raise ConflictError(
                message="A driver profile already exists for this user.",
                details={"user_id": user_id},
            )

        driver = self.driver_repo.create(
            user_id=user_id,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            license_number=license_number,
            operating_area=operating_area,
        )
        db.session.commit()
        return driver

    def get_driver(self, driver_id):
        """Get a driver by ID.

        Args:
            driver_id: UUID of the driver.

        Returns:
            Driver instance.

        Raises:
            NotFoundError: If driver not found.
        """
        driver = self.driver_repo.get_by_id(driver_id)
        if driver is None:
            raise NotFoundError(
                message=f"Driver with id '{driver_id}' not found.",
            )
        return driver

    def list_drivers(self, page=1, per_page=20, filters=None, sort_by=None):
        """List drivers with pagination and filtering.

        Args:
            page: Page number.
            per_page: Items per page.
            filters: Optional filters dict.
            sort_by: Sort field string.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        return self.driver_repo.list_drivers(
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by,
        )

    def update_driver(self, driver_id, **kwargs):
        """Update a driver's profile fields.

        Args:
            driver_id: UUID of the driver to update.
            **kwargs: Fields to update.

        Returns:
            The updated Driver instance.

        Raises:
            NotFoundError: If driver not found.
        """
        driver = self.driver_repo.get_by_id(driver_id)
        if driver is None:
            raise NotFoundError(
                message=f"Driver with id '{driver_id}' not found.",
            )

        updated = self.driver_repo.update(driver_id, **kwargs)
        db.session.commit()
        return updated

    def assign_to_booking(self, booking_id, driver_id, assigned_by):
        """Assign a driver to a booking.

        Checks for scheduling conflicts, updates driver availability for
        the booking date range, and creates a BookingDriver record.

        Args:
            booking_id: UUID of the booking.
            driver_id: UUID of the driver.
            assigned_by: UUID of the admin performing the assignment.

        Returns:
            The created BookingDriver record.

        Raises:
            NotFoundError: If booking or driver not found.
            ConflictError: If driver has overlapping assignments (HTTP 409).
        """
        # Verify booking exists
        booking = self.booking_repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError(
                message=f"Booking with id '{booking_id}' not found.",
            )

        # Verify driver exists
        driver = self.driver_repo.get_by_id(driver_id)
        if driver is None:
            raise NotFoundError(
                message=f"Driver with id '{driver_id}' not found.",
            )

        # Check for scheduling conflicts
        conflicts = self.driver_repo.check_conflicts(
            driver_id=driver_id,
            start_date=booking.travel_start_date,
            end_date=booking.travel_end_date,
        )

        if conflicts:
            conflicting_dates = [d.isoformat() for d in conflicts]
            raise ConflictError(
                message="Driver has overlapping assignment for the requested dates.",
                details={
                    "driver_id": driver_id,
                    "conflicting_dates": conflicting_dates,
                },
            )

        # Update driver availability (mark as unavailable for booking dates)
        self.driver_repo.update_availability(
            driver_id=driver_id,
            start_date=booking.travel_start_date,
            end_date=booking.travel_end_date,
            is_available=False,
        )

        # Create the BookingDriver assignment record
        booking_driver = self.driver_repo.create_booking_driver(
            booking_id=booking_id,
            driver_id=driver_id,
            assigned_by=assigned_by,
        )

        # Increment total assignments
        driver.total_assignments = (driver.total_assignments or 0) + 1

        db.session.commit()
        return booking_driver

    def rate_driver(self, driver_id, rating):
        """Submit a rating for a driver and update their average.

        Uses a simple incremental average calculation:
        new_avg = (old_avg * (n-1) + new_rating) / n
        where n is total_assignments (used as a proxy for number of ratings).

        Args:
            driver_id: UUID of the driver.
            rating: Integer rating value (1-5).

        Returns:
            The updated Driver instance.

        Raises:
            NotFoundError: If driver not found.
            ValidationError: If rating is not between 1 and 5.
        """
        if rating < 1 or rating > 5:
            raise ValidationError(
                message="Rating must be between 1 and 5.",
                details={"rating": ["Must be between 1 and 5."]},
            )

        driver = self.driver_repo.get_by_id(driver_id)
        if driver is None:
            raise NotFoundError(
                message=f"Driver with id '{driver_id}' not found.",
            )

        # Calculate new average rating
        current_avg = float(driver.average_rating or 0)
        total = driver.total_assignments or 1

        # Use total_assignments as a proxy count for ratings received
        # New average = ((old_avg * (total - 1)) + new_rating) / total
        if total <= 1:
            new_avg = float(rating)
        else:
            new_avg = ((current_avg * (total - 1)) + rating) / total

        # Clamp to 0.00 - 5.00 range
        new_avg = max(0.0, min(5.0, new_avg))

        driver.average_rating = Decimal(str(round(new_avg, 2)))
        db.session.commit()
        return driver

    def check_conflicts(self, driver_id, start_date, end_date):
        """Check if a driver has scheduling conflicts for a date range.

        Args:
            driver_id: UUID of the driver.
            start_date: Start date of the range.
            end_date: End date of the range.

        Returns:
            List of conflicting dates.

        Raises:
            NotFoundError: If driver not found.
        """
        driver = self.driver_repo.get_by_id(driver_id)
        if driver is None:
            raise NotFoundError(
                message=f"Driver with id '{driver_id}' not found.",
            )

        return self.driver_repo.check_conflicts(
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date,
        )
