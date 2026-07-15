"""Hotel service with business logic for hotel, room type, and availability management.

Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
- 8.1: Register hotel with name, address, star rating, amenities, contact, partner association
- 8.2: Store room type details (name, capacity, base price, description, amenities)
- 8.3: Record available room count per room type for specified dates
- 8.4: Return hotels with available rooms matching destination and date criteria
- 8.5: Reject availability setting for past dates with HTTP 422
"""

from datetime import date, timedelta

from flask import g

from app.extensions import db
from app.repositories.hotel_repository import HotelRepository
from app.utils.exceptions import NotFoundError, ValidationError


class HotelService:
    """Service layer for hotel, room type, and availability operations."""

    def __init__(self):
        self.hotel_repo = HotelRepository(db.session)

    def register_hotel(
        self,
        partner_user_id,
        name,
        address,
        destination_id,
        star_rating,
        amenities=None,
        contact_email=None,
        contact_phone=None,
        description=None,
    ):
        """Register a new hotel.

        Args:
            partner_user_id: UUID of the hotel partner user.
            name: Hotel name.
            address: Full address text.
            destination_id: UUID of the destination.
            star_rating: Integer 1-5.
            amenities: Optional list of amenities.
            contact_email: Optional contact email.
            contact_phone: Optional contact phone.
            description: Optional description.

        Returns:
            The created Hotel instance.

        Raises:
            ValidationError: If star_rating is not between 1 and 5.
        """
        if star_rating < 1 or star_rating > 5:
            raise ValidationError(
                message="Star rating must be between 1 and 5.",
                details={"star_rating": ["Must be between 1 and 5."]},
            )

        hotel = self.hotel_repo.create(
            partner_user_id=partner_user_id,
            name=name,
            address=address,
            destination_id=destination_id,
            star_rating=star_rating,
            amenities=amenities,
            contact_email=contact_email,
            contact_phone=contact_phone,
            description=description,
        )
        db.session.commit()
        return hotel

    def get_hotel(self, hotel_id):
        """Get a hotel by ID.

        Args:
            hotel_id: UUID of the hotel.

        Returns:
            Hotel instance.

        Raises:
            NotFoundError: If hotel not found.
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if hotel is None:
            raise NotFoundError(
                message=f"Hotel with id '{hotel_id}' not found.",
            )
        return hotel

    def list_hotels(self, page=1, per_page=20, filters=None, sort_by=None):
        """List hotels with pagination and filtering.

        Args:
            page: Page number.
            per_page: Items per page.
            filters: Optional filters dict.
            sort_by: Sort field string.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        return self.hotel_repo.list_hotels(
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by,
        )

    def update_hotel(self, hotel_id, **kwargs):
        """Update a hotel's fields.

        Args:
            hotel_id: UUID of the hotel to update.
            **kwargs: Fields to update.

        Returns:
            The updated Hotel instance.

        Raises:
            NotFoundError: If hotel not found.
            ValidationError: If star_rating is invalid.
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if hotel is None:
            raise NotFoundError(
                message=f"Hotel with id '{hotel_id}' not found.",
            )

        if "star_rating" in kwargs:
            rating = kwargs["star_rating"]
            if rating < 1 or rating > 5:
                raise ValidationError(
                    message="Star rating must be between 1 and 5.",
                    details={"star_rating": ["Must be between 1 and 5."]},
                )

        updated = self.hotel_repo.update(hotel_id, **kwargs)
        db.session.commit()
        return updated

    def add_room_type(
        self,
        hotel_id,
        name,
        capacity,
        base_price,
        description=None,
        amenities=None,
    ):
        """Add a room type to a hotel.

        Args:
            hotel_id: UUID of the hotel.
            name: Room type name.
            capacity: Maximum number of guests.
            base_price: Base price per night.
            description: Optional description.
            amenities: Optional list of amenities.

        Returns:
            The created RoomType instance.

        Raises:
            NotFoundError: If hotel not found.
            ValidationError: If capacity or base_price are invalid.
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if hotel is None:
            raise NotFoundError(
                message=f"Hotel with id '{hotel_id}' not found.",
            )

        if capacity < 1:
            raise ValidationError(
                message="Capacity must be at least 1.",
                details={"capacity": ["Must be at least 1."]},
            )

        if base_price <= 0:
            raise ValidationError(
                message="Base price must be greater than 0.",
                details={"base_price": ["Must be greater than 0."]},
            )

        room_type = self.hotel_repo.create_room_type(
            hotel_id=hotel_id,
            name=name,
            capacity=capacity,
            base_price=base_price,
            description=description,
            amenities=amenities,
        )
        db.session.commit()
        return room_type

    def update_room_type(self, hotel_id, room_type_id, **kwargs):
        """Update a room type's fields.

        Args:
            hotel_id: UUID of the hotel.
            room_type_id: UUID of the room type.
            **kwargs: Fields to update.

        Returns:
            The updated RoomType instance.

        Raises:
            NotFoundError: If hotel or room type not found.
            ValidationError: If capacity or base_price are invalid.
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if hotel is None:
            raise NotFoundError(
                message=f"Hotel with id '{hotel_id}' not found.",
            )

        room_type = self.hotel_repo.get_room_type_for_hotel(hotel_id, room_type_id)
        if room_type is None:
            raise NotFoundError(
                message=f"Room type with id '{room_type_id}' not found for this hotel.",
            )

        if "capacity" in kwargs and kwargs["capacity"] < 1:
            raise ValidationError(
                message="Capacity must be at least 1.",
                details={"capacity": ["Must be at least 1."]},
            )

        if "base_price" in kwargs and kwargs["base_price"] <= 0:
            raise ValidationError(
                message="Base price must be greater than 0.",
                details={"base_price": ["Must be greater than 0."]},
            )

        updated = self.hotel_repo.update_room_type(room_type_id, **kwargs)
        db.session.commit()
        return updated

    def set_availability(self, hotel_id, room_type_id, dates_availability):
        """Set room availability for specified dates.

        Rejects setting availability for past dates (Requirement 8.5).

        Args:
            hotel_id: UUID of the hotel.
            room_type_id: UUID of the room type.
            dates_availability: List of dicts with 'date' and 'available_count' keys.

        Returns:
            List of RoomAvailability instances (created or updated).

        Raises:
            NotFoundError: If hotel or room type not found.
            ValidationError: If any date is in the past.
        """
        # Validate dates first (fail fast on invalid input - Requirement 8.5)
        today = date.today()
        past_dates = [
            entry["date"].isoformat() if isinstance(entry["date"], date) else entry["date"]
            for entry in dates_availability
            if (entry["date"] if isinstance(entry["date"], date) else date.fromisoformat(entry["date"])) < today
        ]

        if past_dates:
            raise ValidationError(
                message="Cannot set availability for past dates.",
                details={"dates": past_dates},
            )

        hotel = self.hotel_repo.get_by_id(hotel_id)
        if hotel is None:
            raise NotFoundError(
                message=f"Hotel with id '{hotel_id}' not found.",
            )

        room_type = self.hotel_repo.get_room_type_for_hotel(hotel_id, room_type_id)
        if room_type is None:
            raise NotFoundError(
                message=f"Room type with id '{room_type_id}' not found for this hotel.",
            )

        results = []
        for entry in dates_availability:
            avail_date = entry["date"] if isinstance(entry["date"], date) else date.fromisoformat(entry["date"])
            available_count = entry["available_count"]
            availability = self.hotel_repo.set_availability(
                room_type_id=room_type_id,
                date=avail_date,
                available_count=available_count,
            )
            results.append(availability)

        db.session.commit()
        return results

    def query_availability(
        self,
        destination_id,
        check_in,
        check_out,
        min_capacity=1,
        page=1,
        per_page=20,
    ):
        """Query available hotels for a destination and date range.

        Args:
            destination_id: UUID of the destination.
            check_in: Check-in date (inclusive).
            check_out: Check-out date (exclusive).
            min_capacity: Minimum room capacity.
            page: Page number.
            per_page: Items per page.

        Returns:
            Tuple of (results, pagination_metadata).

        Raises:
            ValidationError: If date range is invalid.
        """
        if check_in >= check_out:
            raise ValidationError(
                message="Check-out date must be after check-in date.",
                details={"check_out": ["Must be after check_in date."]},
            )

        return self.hotel_repo.query_availability(
            destination_id=destination_id,
            check_in=check_in,
            check_out=check_out,
            min_capacity=min_capacity,
            page=page,
            per_page=per_page,
        )
