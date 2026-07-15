"""Scout request/response schemas for validation and serialization.

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 26.1
- 9.1: Scout creation fields (user_id, languages, specializations, operating_area, is_available)
- 9.2: Scout assignment to booking (scout_id)
- 9.3: Assignment record fields (booking_id, scout_id, assigned_at, assigned_by)
- 9.4: Rating fields (rating 1-5, review_text)
- 9.5: Scout listing response with availability, average_rating, total_assignments
- 26.1: Schema-based validation via Marshmallow
"""

from marshmallow import Schema, fields, validate


# --- Request Schemas ---


class CreateScoutSchema(Schema):
    """Schema for creating a scout profile.

    Required: user_id, languages, operating_area
    Optional: specializations, is_available
    """

    user_id = fields.String(
        required=True,
        error_messages={"required": "User ID is required."},
    )
    languages = fields.List(
        fields.String(),
        required=True,
        validate=validate.Length(min=1, error="At least one language is required."),
        error_messages={"required": "Languages are required."},
    )
    specializations = fields.List(
        fields.String(),
        required=False,
        load_default=None,
    )
    operating_area = fields.String(
        required=True,
        validate=validate.OneOf(
            ["varanasi", "mirzapur"],
            error="Operating area must be 'varanasi' or 'mirzapur'.",
        ),
        error_messages={"required": "Operating area is required."},
    )
    is_available = fields.Boolean(
        required=False,
        load_default=True,
    )


class UpdateScoutSchema(Schema):
    """Schema for updating a scout profile.

    All fields optional.
    """

    languages = fields.List(
        fields.String(),
        required=False,
        validate=validate.Length(min=1, error="At least one language is required."),
    )
    specializations = fields.List(
        fields.String(),
        required=False,
        allow_none=True,
    )
    operating_area = fields.String(
        required=False,
        validate=validate.OneOf(
            ["varanasi", "mirzapur"],
            error="Operating area must be 'varanasi' or 'mirzapur'.",
        ),
    )
    is_available = fields.Boolean(required=False)


class AssignScoutSchema(Schema):
    """Schema for assigning a scout to a booking.

    Required: scout_id
    """

    scout_id = fields.String(
        required=True,
        error_messages={"required": "Scout ID is required."},
    )


class RateScoutSchema(Schema):
    """Schema for rating a scout.

    Required: booking_id, rating
    Optional: review_text
    """

    booking_id = fields.String(
        required=True,
        error_messages={"required": "Booking ID is required."},
    )
    rating = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=5, error="Rating must be between 1 and 5."),
        error_messages={"required": "Rating is required."},
    )
    review_text = fields.String(
        required=False,
        load_default=None,
    )


# --- Response Schemas ---


class ScoutResponseSchema(Schema):
    """Schema for serializing a scout in responses."""

    id = fields.String(dump_only=True)
    user_id = fields.String(dump_only=True)
    languages = fields.List(fields.String(), dump_only=True)
    specializations = fields.List(fields.String(), dump_only=True)
    operating_area = fields.Method("get_operating_area")
    is_available = fields.Boolean(dump_only=True)
    average_rating = fields.Float(dump_only=True)
    total_assignments = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_operating_area(self, obj):
        """Serialize the operating_area enum to its string value."""
        if obj.operating_area:
            return obj.operating_area.value
        return None


class BookingScoutResponseSchema(Schema):
    """Schema for serializing a booking-scout assignment in responses."""

    id = fields.String(dump_only=True)
    booking_id = fields.String(dump_only=True)
    scout_id = fields.String(dump_only=True)
    assigned_at = fields.DateTime(dump_only=True)
    assigned_by = fields.String(dump_only=True)


class ScoutRatingResponseSchema(Schema):
    """Schema for serializing a scout rating response."""

    id = fields.String(dump_only=True)
    customer_id = fields.String(dump_only=True)
    booking_id = fields.String(dump_only=True)
    entity_type = fields.Method("get_entity_type")
    entity_id = fields.String(dump_only=True)
    rating = fields.Integer(dump_only=True)
    body = fields.String(dump_only=True)
    status = fields.Method("get_status")
    created_at = fields.DateTime(dump_only=True)

    def get_entity_type(self, obj):
        """Serialize the entity_type enum to its string value."""
        if obj.entity_type:
            return obj.entity_type.value if hasattr(obj.entity_type, 'value') else str(obj.entity_type)
        return None

    def get_status(self, obj):
        """Serialize the status enum to its string value."""
        if obj.status:
            return obj.status.value if hasattr(obj.status, 'value') else str(obj.status)
        return None
