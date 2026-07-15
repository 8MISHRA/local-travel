"""Hotel request/response schemas for validation and serialization.

Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 26.1
- 8.1: Hotel creation fields (name, address, star_rating, amenities, contact, partner)
- 8.2: Room type fields (name, capacity, base_price, description, amenities)
- 8.3: Availability fields (date, available_count)
- 8.4: Availability query params (destination_id, check_in, check_out, min_capacity)
- 8.5: Reject past dates for availability setting
- 26.1: Schema-based validation via Marshmallow
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError


# --- Request Schemas ---


class CreateHotelSchema(Schema):
    """Schema for creating a hotel.

    Required: partner_user_id, name, address, destination_id, star_rating
    Optional: amenities, contact_email, contact_phone, description
    """

    partner_user_id = fields.String(
        required=True,
        error_messages={"required": "Partner user ID is required."},
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error="Name must be between 1 and 255 characters."),
        error_messages={"required": "Hotel name is required."},
    )
    address = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Address is required."),
        error_messages={"required": "Address is required."},
    )
    destination_id = fields.String(
        required=True,
        error_messages={"required": "Destination ID is required."},
    )
    star_rating = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=5, error="Star rating must be between 1 and 5."),
        error_messages={"required": "Star rating is required."},
    )
    amenities = fields.List(
        fields.String(),
        required=False,
        load_default=None,
    )
    contact_email = fields.Email(
        required=False,
        load_default=None,
    )
    contact_phone = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=20, error="Phone must not exceed 20 characters."),
    )
    description = fields.String(
        required=False,
        load_default=None,
    )


class UpdateHotelSchema(Schema):
    """Schema for updating a hotel.

    All fields optional.
    """

    name = fields.String(
        required=False,
        validate=validate.Length(min=1, max=255, error="Name must be between 1 and 255 characters."),
    )
    address = fields.String(
        required=False,
        validate=validate.Length(min=1, error="Address cannot be empty."),
    )
    star_rating = fields.Integer(
        required=False,
        validate=validate.Range(min=1, max=5, error="Star rating must be between 1 and 5."),
    )
    amenities = fields.List(fields.String(), required=False)
    contact_email = fields.Email(required=False, allow_none=True)
    contact_phone = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=20, error="Phone must not exceed 20 characters."),
    )
    description = fields.String(required=False, allow_none=True)
    is_active = fields.Boolean(required=False)


class CreateRoomTypeSchema(Schema):
    """Schema for creating a room type.

    Required: name, capacity, base_price
    Optional: description, amenities
    """

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters."),
        error_messages={"required": "Room type name is required."},
    )
    capacity = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Capacity must be at least 1."),
        error_messages={"required": "Capacity is required."},
    )
    base_price = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Base price must be greater than 0."),
        error_messages={"required": "Base price is required."},
    )
    description = fields.String(
        required=False,
        load_default=None,
    )
    amenities = fields.List(
        fields.String(),
        required=False,
        load_default=None,
    )


class UpdateRoomTypeSchema(Schema):
    """Schema for updating a room type.

    All fields optional.
    """

    name = fields.String(
        required=False,
        validate=validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters."),
    )
    capacity = fields.Integer(
        required=False,
        validate=validate.Range(min=1, error="Capacity must be at least 1."),
    )
    base_price = fields.Float(
        required=False,
        validate=validate.Range(min=0.01, error="Base price must be greater than 0."),
    )
    description = fields.String(required=False, allow_none=True)
    amenities = fields.List(fields.String(), required=False)


class AvailabilityEntrySchema(Schema):
    """Schema for a single availability entry (date + count)."""

    date = fields.Date(
        required=True,
        error_messages={"required": "Date is required."},
    )
    available_count = fields.Integer(
        required=True,
        validate=validate.Range(min=0, error="Available count must be 0 or greater."),
        error_messages={"required": "Available count is required."},
    )


class SetAvailabilitySchema(Schema):
    """Schema for setting room availability.

    Required: room_type_id, availability (list of date/count pairs)
    """

    room_type_id = fields.String(
        required=True,
        error_messages={"required": "Room type ID is required."},
    )
    availability = fields.List(
        fields.Nested(AvailabilityEntrySchema),
        required=True,
        validate=validate.Length(min=1, error="At least one availability entry is required."),
        error_messages={"required": "Availability entries are required."},
    )


class AvailabilityQuerySchema(Schema):
    """Schema for querying hotel availability.

    Required: destination_id, check_in, check_out
    Optional: min_capacity, page, per_page
    """

    destination_id = fields.String(
        required=True,
        error_messages={"required": "Destination ID is required."},
    )
    check_in = fields.Date(
        required=True,
        error_messages={"required": "Check-in date is required."},
    )
    check_out = fields.Date(
        required=True,
        error_messages={"required": "Check-out date is required."},
    )
    min_capacity = fields.Integer(
        required=False,
        load_default=1,
        validate=validate.Range(min=1, error="Minimum capacity must be at least 1."),
    )
    page = fields.Integer(required=False, load_default=1)
    per_page = fields.Integer(required=False, load_default=20)


# --- Response Schemas ---


class RoomTypeResponseSchema(Schema):
    """Schema for serializing a room type in responses."""

    id = fields.String(dump_only=True)
    hotel_id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    capacity = fields.Integer(dump_only=True)
    base_price = fields.Float(dump_only=True)
    description = fields.String(dump_only=True)
    amenities = fields.List(fields.String(), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class HotelResponseSchema(Schema):
    """Schema for serializing a hotel in responses."""

    id = fields.String(dump_only=True)
    partner_user_id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    address = fields.String(dump_only=True)
    destination_id = fields.String(dump_only=True)
    star_rating = fields.Integer(dump_only=True)
    amenities = fields.List(fields.String(), dump_only=True)
    contact_email = fields.String(dump_only=True)
    contact_phone = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class HotelDetailResponseSchema(HotelResponseSchema):
    """Schema for serializing a hotel with room types."""

    room_types = fields.List(
        fields.Nested(RoomTypeResponseSchema),
        dump_only=True,
    )


class RoomAvailabilityResponseSchema(Schema):
    """Schema for serializing room availability in responses."""

    id = fields.String(dump_only=True)
    room_type_id = fields.String(dump_only=True)
    date = fields.Date(dump_only=True)
    available_count = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AvailabilityResultSchema(Schema):
    """Schema for serializing availability query results."""

    hotel = fields.Nested(HotelResponseSchema, dump_only=True)
    room_type = fields.Nested(RoomTypeResponseSchema, dump_only=True)
