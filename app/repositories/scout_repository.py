"""Scout repository for data access operations on scouts and scout availability.

Validates: Requirements 9.1, 9.2, 9.3, 9.5
- 9.1: Scout profile CRUD with languages, specializations, operating area
- 9.2: Availability checks for scout assignment
- 9.3: Assignment tracking via BookingScout records
- 9.5: Listing scouts with availability, average rating, and assignment count
"""

import math
from datetime import datetime, timezone

from sqlalchemy import func

from app.models.booking import BookingScout
from app.models.scout import Scout, ScoutAvailability
from app.repositories.base_repository import BaseRepository


class ScoutRepository(BaseRepository):
    """Repository for Scout model with availability and assignment support."""

    model_class = Scout

    def list_scouts(self, page=1, per_page=20, filters=None, sort_by=None):
        """Return paginated list of scouts with ratings and assignment counts.

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

        query = self.session.query(Scout)

        if filters:
            query = self._apply_filters(query, filters)

        if sort_by:
            query = self._apply_sorting(query, sort_by)
        else:
            query = query.order_by(Scout.created_at.desc())

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

    def is_available_for_dates(self, scout_id, start_date, end_date):
        """Check if a scout is available for all dates in the given range.

        A scout is considered available for a date if:
        - No ScoutAvailability record exists for that date (default available), OR
        - A ScoutAvailability record exists with is_available=True

        Args:
            scout_id: UUID of the scout.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            True if the scout is available for all dates in the range.
        """
        from datetime import timedelta

        num_days = (end_date - start_date).days + 1

        # Count dates where scout is explicitly marked as unavailable
        unavailable_count = self.session.query(ScoutAvailability).filter(
            ScoutAvailability.scout_id == scout_id,
            ScoutAvailability.date >= start_date,
            ScoutAvailability.date <= end_date,
            ScoutAvailability.is_available.is_(False),
        ).count()

        return unavailable_count == 0

    def set_unavailable_for_dates(self, scout_id, start_date, end_date):
        """Mark a scout as unavailable for all dates in the given range.

        Uses upsert logic: if a record exists for (scout_id, date), update it;
        otherwise create a new one.

        Args:
            scout_id: UUID of the scout.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).

        Returns:
            List of ScoutAvailability records created/updated.
        """
        from datetime import timedelta

        results = []
        current_date = start_date
        while current_date <= end_date:
            existing = self.session.query(ScoutAvailability).filter(
                ScoutAvailability.scout_id == scout_id,
                ScoutAvailability.date == current_date,
            ).first()

            if existing:
                existing.is_available = False
                results.append(existing)
            else:
                availability = ScoutAvailability(
                    scout_id=scout_id,
                    date=current_date,
                    is_available=False,
                )
                self.session.add(availability)
                results.append(availability)

            current_date += timedelta(days=1)

        self.session.flush()
        return results

    def create_booking_scout(self, booking_id, scout_id, assigned_by):
        """Create a BookingScout assignment record.

        Args:
            booking_id: UUID of the booking.
            scout_id: UUID of the scout.
            assigned_by: UUID of the admin who made the assignment.

        Returns:
            The created BookingScout instance.
        """
        booking_scout = BookingScout(
            booking_id=booking_id,
            scout_id=scout_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
        )
        self.session.add(booking_scout)
        self.session.flush()
        return booking_scout

    def get_booking_scout(self, booking_id, scout_id):
        """Check if a scout is already assigned to a booking.

        Args:
            booking_id: UUID of the booking.
            scout_id: UUID of the scout.

        Returns:
            BookingScout instance or None.
        """
        return self.session.query(BookingScout).filter(
            BookingScout.booking_id == booking_id,
            BookingScout.scout_id == scout_id,
        ).first()

    def get_assignment_count(self, scout_id):
        """Get the total number of booking assignments for a scout.

        Args:
            scout_id: UUID of the scout.

        Returns:
            Integer count of assignments.
        """
        return self.session.query(BookingScout).filter(
            BookingScout.scout_id == scout_id,
        ).count()

    def update_rating(self, scout_id, new_average_rating):
        """Update a scout's average rating.

        Args:
            scout_id: UUID of the scout.
            new_average_rating: The new calculated average rating.

        Returns:
            The updated Scout instance or None.
        """
        scout = self.session.query(Scout).filter(
            Scout.id == scout_id,
        ).first()
        if scout:
            scout.average_rating = new_average_rating
            self.session.flush()
        return scout

    def increment_assignments(self, scout_id):
        """Increment a scout's total_assignments counter.

        Args:
            scout_id: UUID of the scout.

        Returns:
            The updated Scout instance or None.
        """
        scout = self.session.query(Scout).filter(
            Scout.id == scout_id,
        ).first()
        if scout:
            scout.total_assignments = (scout.total_assignments or 0) + 1
            self.session.flush()
        return scout
