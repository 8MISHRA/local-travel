"""Booking request/response schemas for validation and serialization.

Validates: Requirements 7.1, 7.2, 7.5, 7.6, 7.7, 26.1
- 7.1: Create draft booking with package, dates, travellers
- 7.2: Submit booking details (hotel, transport, add-ons)
- 7.5: Cancel booking
- 7.6: Admin/scout status update with timestamp and acting user
- 7.7: Customer-scoped listing with pagination and status filtering
- 26.1: Schema-based input validation via Marshmallow
"""

from marshmallow import Schema, fields, validate

from app.models.booking import BookingStatus

# Valid booking status values for validation
VALID_BOOKING_STATUSES = [s.value for s in BookingStatus]

# Valid traveller types
VALID_TRAVELLER_TYPES = ["solo", "couple", "family", "group", "corporate"]


# --- Request Schemas ---


class BookingCreateSchema(Schema):
    """Schema for creating a draft booking.

    Required: package_id, travel_start_date, travel_end_date,
              num_travellers, traveller_type
    Optional: special_requests
    """

    package_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=36),
        error_messages={"required": "Package ID is required."},
    )
    travel_start_date = fields.Date(
        required=True,
        error_messages={"required": "Travel start date is required."},
    )
    travel_end_date = fields.Date(
        required=True,
        error_messages={"required": "Travel end date is required."},
    )
    num_travellers = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Number of travellers must be at least 1."),
        error_messages={"required": "Number of travellers is required."},
    )
    traveller_type = fields.String(
        required=True,
        validate=validate.OneOf(
            VALID_TRAVELLER_TYPES,
            error="Traveller type must be one of: {choices}.",
        ),
        error_messages={"required": "Traveller type is required."},
    )
    special_requests = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
    )


class BookingUpdateSchema(Schema):
    """Schema for updating booking details (before submission).

    All fields are optional. Only provided fields will be updated.
    Used for PATCH /bookings/{id} to update draft booking details.
    """

    hotel_preference_id = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=36),
    )
    room_type_id = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=36),
    )
    transport_preferences = fields.Dict(
        required=False,
        load_default=None,
        allow_none=True,
    )
    add_ons = fields.List(
        fields.String(),
        required=False,
        load_default=None,
        allow_none=True,
    )
    special_requests = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
    )
    num_travellers = fields.Integer(
        required=False,
        validate=validate.Range(min=1, error="Number of travellers must be at least 1."),
    )
    traveller_type = fields.String(
        required=False,
        validate=validate.OneOf(
            VALID_TRAVELLER_TYPES,
            error="Traveller type must be one of: {choices}.",
        ),
    )


class BookingStatusSchema(Schema):
    """Schema for admin/scout status updates.

    Required: status
    Optional: notes
    """

    status = fields.String(
        required=True,
        validate=validate.OneOf(
            VALID_BOOKING_STATUSES,
            error="Status must be one of: {choices}.",
        ),
        error_messages={"required": "Status is required."},
    )
    notes = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
    )


# --- Response Schemas ---


class BookingResponseSchema(Schema):
    """Schema for serializing booking data in responses."""

    id = fields.String(dump_only=True)
    booking_number = fields.String(dump_only=True)
    customer_id = fields.String(dump_only=True)
    package_id = fields.String(dump_only=True)
    status = fields.Method("get_status")
    travel_start_date = fields.Date(dump_only=True)
    travel_end_date = fields.Date(dump_only=True)
    num_travellers = fields.Integer(dump_only=True)
    traveller_type = fields.String(dump_only=True)
    hotel_preference_id = fields.String(dump_only=True, allow_none=True)
    room_type_id = fields.String(dump_only=True, allow_none=True)
    transport_preferences = fields.Dict(dump_only=True, allow_none=True)
    add_ons = fields.List(fields.String(), dump_only=True, allow_none=True)
    subtotal = fields.Float(dump_only=True, allow_none=True)
    discount_amount = fields.Float(dump_only=True, allow_none=True)
    tax_amount = fields.Float(dump_only=True, allow_none=True)
    total_amount = fields.Float(dump_only=True, allow_none=True)
    coupon_id = fields.String(dump_only=True, allow_none=True)
    special_requests = fields.String(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):
        """Serialize booking status enum to its string value."""
        if obj.status:
            return obj.status.value if hasattr(obj.status, "value") else str(obj.status)
        return None


class BookingListSchema(Schema):
    """Schema for serializing bookings in list responses (lighter)."""

    id = fields.String(dump_only=True)
    booking_number = fields.String(dump_only=True)
    package_id = fields.String(dump_only=True)
    status = fields.Method("get_status")
    travel_start_date = fields.Date(dump_only=True)
    travel_end_date = fields.Date(dump_only=True)
    num_travellers = fields.Integer(dump_only=True)
    traveller_type = fields.String(dump_only=True)
    total_amount = fields.Float(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):
        """Serialize booking status enum to its string value."""
        if obj.status:
            return obj.status.value if hasattr(obj.status, "value") else str(obj.status)
        return None
