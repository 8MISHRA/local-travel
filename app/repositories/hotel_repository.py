"""Hotel repository for data access operations on hotels, room types, and availability.

Validates: Requirements 8.1, 8.2, 8.3, 8.4
- 8.1: Hotel CRUD with partner association
- 8.2: Room type management per hotel
- 8.3: Room availability per room type and date
- 8.4: Availability query by destination, date range, and room capacity
"""

import math

from sqlalchemy import and_

from app.models.hotel import Hotel, RoomAvailability, RoomType
from app.repositories.base_repository import BaseRepository


class HotelRepository(BaseRepository):
    """Repository for Hotel model with availability query support."""

    model_class = Hotel

    def list_hotels(self, page=1, per_page=20, filters=None, sort_by=None):
        """Return paginated list of active, non-deleted hotels.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (max 100).
            filters: Dict of equality filters (destination_id, is_active, etc.)
            sort_by: Sort field string.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        query = self.session.query(Hotel).filter(
            Hotel.deleted_at.is_(None),
        )

        if filters:
            query = self._apply_filters(query, filters)

        if sort_by:
            query = self._apply_sorting(query, sort_by)
        else:
            query = query.order_by(Hotel.created_at.desc())

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

    def query_availability(
        self,
        destination_id,
        check_in,
        check_out,
        min_capacity=1,
        page=1,
        per_page=20,
    ):
        """Query hotels with available rooms for a destination and date range.

        Finds hotels in the given destination that have at least one room type
        with capacity >= min_capacity AND available_count > 0 for ALL dates in
        the [check_in, check_out) range.

        Args:
            destination_id: UUID of the destination.
            check_in: Start date (inclusive).
            check_out: End date (exclusive).
            min_capacity: Minimum room capacity required.
            page: Page number.
            per_page: Items per page.

        Returns:
            Tuple of (list of dicts with hotel and room info, pagination_metadata).
        """
        from sqlalchemy import func
        from datetime import timedelta

        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        # Calculate number of nights (dates in the range)
        num_nights = (check_out - check_in).days
        if num_nights <= 0:
            return [], {"total": 0, "page": page, "per_page": per_page, "total_pages": 0}

        # Find room types that:
        # 1. Belong to an active, non-deleted hotel in the destination
        # 2. Have capacity >= min_capacity
        # 3. Have availability records with available_count > 0 for ALL dates in range
        subquery = (
            self.session.query(
                RoomAvailability.room_type_id,
                func.count(RoomAvailability.id).label("available_dates"),
            )
            .filter(
                RoomAvailability.date >= check_in,
                RoomAvailability.date < check_out,
                RoomAvailability.available_count > 0,
            )
            .group_by(RoomAvailability.room_type_id)
            .having(func.count(RoomAvailability.id) >= num_nights)
            .subquery()
        )

        query = (
            self.session.query(Hotel, RoomType)
            .join(RoomType, Hotel.id == RoomType.hotel_id)
            .join(subquery, RoomType.id == subquery.c.room_type_id)
            .filter(
                Hotel.deleted_at.is_(None),
                Hotel.is_active.is_(True),
                Hotel.destination_id == destination_id,
                RoomType.capacity >= min_capacity,
            )
            .order_by(Hotel.name.asc())
        )

        # Count total results
        total = query.count()
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        results = query.offset((page - 1) * per_page).limit(per_page).all()

        pagination_meta = {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

        return results, pagination_meta

    def get_room_type(self, room_type_id):
        """Get a room type by ID.

        Args:
            room_type_id: UUID of the room type.

        Returns:
            RoomType instance or None.
        """
        return self.session.query(RoomType).filter(
            RoomType.id == room_type_id,
        ).first()

    def get_room_type_for_hotel(self, hotel_id, room_type_id):
        """Get a room type by ID belonging to a specific hotel.

        Args:
            hotel_id: UUID of the hotel.
            room_type_id: UUID of the room type.

        Returns:
            RoomType instance or None.
        """
        return self.session.query(RoomType).filter(
            RoomType.id == room_type_id,
            RoomType.hotel_id == hotel_id,
        ).first()

    def create_room_type(self, **kwargs):
        """Create a new room type.

        Args:
            **kwargs: RoomType fields (hotel_id, name, capacity, base_price, etc.)

        Returns:
            The created RoomType instance.
        """
        room_type = RoomType(**kwargs)
        self.session.add(room_type)
        self.session.flush()
        return room_type

    def update_room_type(self, room_type_id, **kwargs):
        """Update a room type's fields.

        Args:
            room_type_id: UUID of the room type to update.
            **kwargs: Fields to update.

        Returns:
            The updated RoomType or None if not found.
        """
        room_type = self.get_room_type(room_type_id)
        if room_type is None:
            return None
        for key, value in kwargs.items():
            if hasattr(room_type, key):
                setattr(room_type, key, value)
        self.session.flush()
        return room_type

    def set_availability(self, room_type_id, date, available_count):
        """Set or update availability for a room type on a specific date.

        Uses upsert logic: if a record exists for (room_type_id, date),
        update it; otherwise create a new one.

        Args:
            room_type_id: UUID of the room type.
            date: The date to set availability for.
            available_count: Number of available rooms.

        Returns:
            The RoomAvailability instance (created or updated).
        """
        existing = self.session.query(RoomAvailability).filter(
            RoomAvailability.room_type_id == room_type_id,
            RoomAvailability.date == date,
        ).first()

        if existing:
            existing.available_count = available_count
            self.session.flush()
            return existing

        availability = RoomAvailability(
            room_type_id=room_type_id,
            date=date,
            available_count=available_count,
        )
        self.session.add(availability)
        self.session.flush()
        return availability
