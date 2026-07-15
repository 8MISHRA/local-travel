"""Property-based tests for hotel availability past date rejection.

**Validates: Requirements 8.5**

Tests:
- Property 13: Hotel availability rejects past dates
"""

import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.hotel_service import HotelService
from app.utils.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Past dates: from yesterday back to 1 year ago
st_past_date = st.dates(
    min_value=date.today() - timedelta(days=365),
    max_value=date.today() - timedelta(days=1),
)

# Future dates: today and forward (up to 1 year)
st_future_date = st.dates(
    min_value=date.today(),
    max_value=date.today() + timedelta(days=365),
)

# Available room count (positive integer)
st_available_count = st.integers(min_value=0, max_value=100)


# ---------------------------------------------------------------------------
# Property 13: Hotel availability rejects past dates
# ---------------------------------------------------------------------------

class TestHotelAvailabilityRejectsPastDates:
    """Property 13: Hotel availability rejects past dates.

    **Validates: Requirements 8.5**

    For any date that is in the past, attempting to set availability always
    fails with a ValidationError (422). Future dates (including today) should
    not be rejected by the date validation logic.
    """

    @settings(max_examples=100)
    @given(
        past_date=st_past_date,
        available_count=st_available_count,
    )
    def test_single_past_date_raises_validation_error(
        self, past_date, available_count
    ):
        """**Validates: Requirements 8.5**

        When a single past date is provided in the dates_availability list,
        set_availability must raise ValidationError with status_code 422.
        """
        service = HotelService.__new__(HotelService)
        service.hotel_repo = MagicMock()

        hotel_id = str(uuid.uuid4())
        room_type_id = str(uuid.uuid4())

        dates_availability = [
            {"date": past_date, "available_count": available_count}
        ]

        with pytest.raises(ValidationError) as exc_info:
            service.set_availability(hotel_id, room_type_id, dates_availability)

        assert exc_info.value.status_code == 422
        assert "past" in exc_info.value.message.lower()

    @settings(max_examples=100)
    @given(
        past_dates=st.lists(st_past_date, min_size=1, max_size=10),
        available_counts=st.lists(st_available_count, min_size=1, max_size=10),
    )
    def test_multiple_past_dates_raises_validation_error(
        self, past_dates, available_counts
    ):
        """**Validates: Requirements 8.5**

        When multiple past dates are provided, set_availability must raise
        ValidationError with status_code 422 and include all past dates in
        the error details.
        """
        service = HotelService.__new__(HotelService)
        service.hotel_repo = MagicMock()

        hotel_id = str(uuid.uuid4())
        room_type_id = str(uuid.uuid4())

        # Pair past_dates with available_counts (cycling if needed)
        dates_availability = [
            {
                "date": past_dates[i % len(past_dates)],
                "available_count": available_counts[i % len(available_counts)],
            }
            for i in range(len(past_dates))
        ]

        with pytest.raises(ValidationError) as exc_info:
            service.set_availability(hotel_id, room_type_id, dates_availability)

        assert exc_info.value.status_code == 422
        # Details should contain the rejected dates
        assert exc_info.value.details is not None
        assert "dates" in exc_info.value.details

    @settings(max_examples=100)
    @given(
        past_date=st_past_date,
        future_date=st_future_date,
        available_count=st_available_count,
    )
    def test_mixed_past_and_future_dates_raises_for_past(
        self, past_date, future_date, available_count
    ):
        """**Validates: Requirements 8.5**

        When a mix of past and future dates is provided, set_availability
        must still raise ValidationError because at least one date is in
        the past. The error details should list only the past date(s).
        """
        service = HotelService.__new__(HotelService)
        service.hotel_repo = MagicMock()

        hotel_id = str(uuid.uuid4())
        room_type_id = str(uuid.uuid4())

        dates_availability = [
            {"date": past_date, "available_count": available_count},
            {"date": future_date, "available_count": available_count},
        ]

        with pytest.raises(ValidationError) as exc_info:
            service.set_availability(hotel_id, room_type_id, dates_availability)

        assert exc_info.value.status_code == 422
        # The past date should appear in error details
        past_dates_in_error = exc_info.value.details["dates"]
        assert past_date.isoformat() in past_dates_in_error
        # The future date should NOT appear in error details
        assert future_date.isoformat() not in past_dates_in_error

    @settings(max_examples=100)
    @given(
        future_date=st_future_date,
        available_count=st_available_count,
    )
    def test_future_date_does_not_raise_validation_error(
        self, future_date, available_count
    ):
        """**Validates: Requirements 8.5**

        When only future dates (including today) are provided,
        set_availability must NOT raise ValidationError for dates.
        It may raise NotFoundError if hotel/room doesn't exist, but
        the date validation specifically should pass.
        """
        service = HotelService.__new__(HotelService)
        service.hotel_repo = MagicMock()
        # Mock hotel and room_type as found so the service proceeds past date check
        service.hotel_repo.get_by_id.return_value = MagicMock(id=str(uuid.uuid4()))
        service.hotel_repo.get_room_type_for_hotel.return_value = MagicMock(
            id=str(uuid.uuid4())
        )
        service.hotel_repo.set_availability.return_value = MagicMock()

        hotel_id = str(uuid.uuid4())
        room_type_id = str(uuid.uuid4())

        dates_availability = [
            {"date": future_date, "available_count": available_count}
        ]

        # Should NOT raise ValidationError - it may need db.session.commit
        # but since we're testing date validation only, patch the commit
        with patch("app.services.hotel_service.db") as mock_db:
            mock_db.session = MagicMock()
            try:
                result = service.set_availability(
                    hotel_id, room_type_id, dates_availability
                )
                # If it returns successfully, the date validation passed
                assert result is not None
            except ValidationError:
                # This should NOT happen for future dates
                pytest.fail(
                    f"ValidationError raised for future/today date {future_date}"
                )

    @settings(max_examples=100)
    @given(
        past_date=st_past_date,
        available_count=st_available_count,
    )
    def test_past_date_as_string_raises_validation_error(
        self, past_date, available_count
    ):
        """**Validates: Requirements 8.5**

        When a past date is provided as an ISO format string instead of a
        date object, set_availability must still reject it with
        ValidationError (422).
        """
        service = HotelService.__new__(HotelService)
        service.hotel_repo = MagicMock()

        hotel_id = str(uuid.uuid4())
        room_type_id = str(uuid.uuid4())

        # Provide date as ISO string instead of date object
        dates_availability = [
            {"date": past_date.isoformat(), "available_count": available_count}
        ]

        with pytest.raises(ValidationError) as exc_info:
            service.set_availability(hotel_id, room_type_id, dates_availability)

        assert exc_info.value.status_code == 422
        assert "past" in exc_info.value.message.lower()
