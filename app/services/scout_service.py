"""Scout service with business logic for scout management and assignment.

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
- 9.1: Create scout profile with languages, specializations, operating area, availability
- 9.2: Assign available scout to booking based on destination and date
- 9.3: Update scout availability for booking dates and record assignment
- 9.4: Store customer rating (1-5) and review text for a scout
- 9.5: List scouts with availability, average rating, and assignment count
"""

from flask import g

from app.extensions import db
from app.models.booking import Booking, BookingStatus
from app.models.review import Review, ReviewEntityType, ReviewStatus
from app.models.scout import Scout
from app.repositories.scout_repository import ScoutRepository
from app.utils.exceptions import ConflictError, NotFoundError, ValidationError


class ScoutService:
    """Service layer for scout operations including assignment and rating."""

    def __init__(self):
        self.scout_repo = ScoutRepository(db.session)

    def create_scout(
        self,
        user_id,
        languages,
        operating_area,
        specializations=None,
        is_available=True,
    ):
        """Create a new scout profile.

        Args:
            user_id: UUID of the associated user account.
            languages: List of languages the scout speaks.
            operating_area: OperatingArea enum value (varanasi or mirzapur).
            specializations: Optional list of specialization areas.
            is_available: Whether the scout is currently available (default True).

        Returns:
            The created Scout instance.

        Raises:
            ValidationError: If languages is empty.
            ConflictError: If a scout profile already exists for this user.
        """
        if not languages:
            raise ValidationError(
                message="At least one language is required.",
                details={"languages": ["At least one language is required."]},
            )

        # Check if scout profile already exists for this user
        existing = db.session.query(Scout).filter(
            Scout.user_id == user_id,
        ).first()
        if existing:
            raise ConflictError(
                message=f"A scout profile already exists for user '{user_id}'.",
            )

        scout = self.scout_repo.create(
            user_id=user_id,
            languages=languages,
            specializations=specializations,
            operating_area=operating_area,
            is_available=is_available,
        )
        db.session.commit()
        return scout

    def get_scout(self, scout_id):
        """Get a scout by ID.

        Args:
            scout_id: UUID of the scout.

        Returns:
            Scout instance.

        Raises:
            NotFoundError: If scout not found.
        """
        scout = db.session.query(Scout).filter(
            Scout.id == scout_id,
        ).first()
        if scout is None:
            raise NotFoundError(
                message=f"Scout with id '{scout_id}' not found.",
            )
        return scout

    def update_scout(self, scout_id, **kwargs):
        """Update a scout's profile fields.

        Args:
            scout_id: UUID of the scout to update.
            **kwargs: Fields to update (languages, specializations, operating_area, is_available).

        Returns:
            The updated Scout instance.

        Raises:
            NotFoundError: If scout not found.
            ValidationError: If languages is set to empty.
        """
        scout = db.session.query(Scout).filter(
            Scout.id == scout_id,
        ).first()
        if scout is None:
            raise NotFoundError(
                message=f"Scout with id '{scout_id}' not found.",
            )

        if "languages" in kwargs and not kwargs["languages"]:
            raise ValidationError(
                message="At least one language is required.",
                details={"languages": ["At least one language is required."]},
            )

        for key, value in kwargs.items():
            if hasattr(scout, key):
                setattr(scout, key, value)

        db.session.flush()
        db.session.commit()
        return scout

    def list_scouts(self, page=1, per_page=20, filters=None, sort_by=None):
        """List scouts with pagination, filtering, and sorting.

        Args:
            page: Page number.
            per_page: Items per page.
            filters: Optional filters dict (operating_area, is_available).
            sort_by: Sort field string.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        return self.scout_repo.list_scouts(
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by,
        )

    def assign_to_booking(self, booking_id, scout_id, assigned_by):
        """Assign a scout to a booking.

        Validates that:
        - The booking exists and is confirmed
        - The scout exists and is generally available
        - The scout is available for the booking dates
        - The scout isn't already assigned to this booking

        Updates the scout's availability for the booking dates and creates
        a BookingScout record.

        Args:
            booking_id: UUID of the booking.
            scout_id: UUID of the scout to assign.
            assigned_by: UUID of the admin making the assignment.

        Returns:
            The created BookingScout instance.

        Raises:
            NotFoundError: If booking or scout not found.
            ValidationError: If booking is not in confirmed status.
            ConflictError: If scout is unavailable or already assigned.
        """
        # Validate booking exists and is confirmed
        booking = db.session.query(Booking).filter(
            Booking.id == booking_id,
            Booking.deleted_at.is_(None),
        ).first()
        if booking is None:
            raise NotFoundError(
                message=f"Booking with id '{booking_id}' not found.",
            )

        if booking.status not in (BookingStatus.confirmed, BookingStatus.in_progress):
            raise ValidationError(
                message="Scout can only be assigned to confirmed or in-progress bookings.",
                details={"status": [f"Current status is '{booking.status.value}'"]},
            )

        # Validate scout exists
        scout = db.session.query(Scout).filter(
            Scout.id == scout_id,
        ).first()
        if scout is None:
            raise NotFoundError(
                message=f"Scout with id '{scout_id}' not found.",
            )

        # Check scout is generally available
        if not scout.is_available:
            raise ConflictError(
                message="Scout is not currently available for assignments.",
            )

        # Check scout is available for the booking dates
        if not self.scout_repo.is_available_for_dates(
            scout_id, booking.travel_start_date, booking.travel_end_date
        ):
            raise ConflictError(
                message="Scout is not available for the booking dates.",
                details={
                    "start_date": booking.travel_start_date.isoformat(),
                    "end_date": booking.travel_end_date.isoformat(),
                },
            )

        # Check scout isn't already assigned to this booking
        existing_assignment = self.scout_repo.get_booking_scout(booking_id, scout_id)
        if existing_assignment:
            raise ConflictError(
                message="Scout is already assigned to this booking.",
            )

        # Mark scout as unavailable for booking dates
        self.scout_repo.set_unavailable_for_dates(
            scout_id, booking.travel_start_date, booking.travel_end_date
        )

        # Create booking-scout assignment record
        booking_scout = self.scout_repo.create_booking_scout(
            booking_id=booking_id,
            scout_id=scout_id,
            assigned_by=assigned_by,
        )

        # Increment assignment count
        self.scout_repo.increment_assignments(scout_id)

        db.session.commit()
        return booking_scout

    def rate_scout(self, scout_id, customer_id, booking_id, rating, review_text=None):
        """Submit a rating for a scout.

        Creates a review record and updates the scout's average rating.

        Args:
            scout_id: UUID of the scout being rated.
            customer_id: UUID of the customer submitting the rating.
            booking_id: UUID of the associated booking.
            rating: Integer rating value (1-5).
            review_text: Optional review text.

        Returns:
            The created Review instance.

        Raises:
            NotFoundError: If scout not found.
            ValidationError: If rating is not 1-5 or booking is not completed.
        """
        # Validate scout exists
        scout = db.session.query(Scout).filter(
            Scout.id == scout_id,
        ).first()
        if scout is None:
            raise NotFoundError(
                message=f"Scout with id '{scout_id}' not found.",
            )

        # Validate rating range
        if rating < 1 or rating > 5:
            raise ValidationError(
                message="Rating must be between 1 and 5.",
                details={"rating": ["Must be between 1 and 5."]},
            )

        # Validate booking exists and is completed
        booking = db.session.query(Booking).filter(
            Booking.id == booking_id,
            Booking.customer_id == customer_id,
            Booking.deleted_at.is_(None),
        ).first()
        if booking is None:
            raise NotFoundError(
                message=f"Booking with id '{booking_id}' not found.",
            )

        if booking.status != BookingStatus.completed:
            raise ValidationError(
                message="Ratings can only be submitted for completed bookings.",
                details={"status": [f"Current status is '{booking.status.value}'"]},
            )

        # Create review record
        review = Review(
            customer_id=customer_id,
            booking_id=booking_id,
            package_id=booking.package_id,
            entity_type=ReviewEntityType.scout,
            entity_id=scout_id,
            rating=rating,
            body=review_text,
            status=ReviewStatus.pending_moderation,
        )
        db.session.add(review)
        db.session.flush()

        # Recalculate average rating for the scout
        from sqlalchemy import func

        avg_result = db.session.query(func.avg(Review.rating)).filter(
            Review.entity_type == ReviewEntityType.scout,
            Review.entity_id == scout_id,
            Review.deleted_at.is_(None),
        ).scalar()

        new_average = round(float(avg_result), 2) if avg_result else 0.00
        self.scout_repo.update_rating(scout_id, new_average)

        db.session.commit()
        return review
