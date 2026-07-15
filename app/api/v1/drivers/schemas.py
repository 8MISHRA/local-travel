"""Driver request/response schemas for validation and serialization.

Validates: Requirements 10.1, 10.2, 10.3, 10.4, 26.1
- 10.1: Driver creation fields (user_id, vehicle_type, vehicle_number, license, area)
- 10.2: Driver assignment to booking
- 10.3: Driver rating (1-5)
- 10.4: Conflict detection response
- 26.1: Schema-based validation via Marshmallow
"""

from marshmallow import Schema, fields, validate


# --- Request Schemas ---


class CreateDriverSchema(Schema):
    """Schema for creating a driver profile.

    Required: user_id, vehicle_type, vehicle_number, license_number, operating_area
    """

    user_id = fields.String(
        required=True,
        error_messages={"required": "User ID is required."},
    )
    vehicle_type = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50, error="Vehicle type must be between 1 and 50 characters."),
        error_messages={"required": "Vehicle type is required."},
    )
    vehicle_number = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20, error="Vehicle number must be between 1 and 20 characters."),
        error_messages={"required": "Vehicle number is required."},
    )
    license_number = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50, error="License number must be between 1 and 50 characters."),
        error_messages={"required": "License number is required."},
    )
    operating_area = fields.String(
        required=True,
        validate=validate.OneOf(
            ["varanasi", "mirzapur"],
            error="Operating area must be 'varanasi' or 'mirzapur'.",
        ),
        error_messages={"required": "Operating area is required."},
    )


class UpdateDriverSchema(Schema):
    """Schema for updating a driver profile.

    All fields optional.
    """

    vehicle_type = fields.String(
        required=False,
        validate=validate.Length(min=1, max=50, error="Vehicle type must be between 1 and 50 characters."),
    )
    vehicle_number = fields.String(
        required=False,
        validate=validate.Length(min=1, max=20, error="Vehicle number must be between 1 and 20 characters."),
    )
    license_number = fields.String(
        required=False,
        validate=validate.Length(min=1, max=50, error="License number must be between 1 and 50 characters."),
    )
    operating_area = fields.String(
        required=False,
        validate=validate.OneOf(
            ["varanasi", "mirzapur"],
            error="Operating area must be 'varanasi' or 'mirzapur'.",
        ),
    )
    is_available = fields.Boolean(required=False)


class AssignDriverSchema(Schema):
    """Schema for assigning a driver to a booking.

    Required: driver_id
    """

    driver_id = fields.String(
        required=True,
        error_messages={"required": "Driver ID is required."},
    )


class RateDriverSchema(Schema):
    """Schema for rating a driver.

    Required: rating (1-5)
    Optional: review_text
    """

    rating = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=5, error="Rating must be between 1 and 5."),
        error_messages={"required": "Rating is required."},
    )
    review_text = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=1000, error="Review text must not exceed 1000 characters."),
    )


# --- Response Schemas ---


class DriverResponseSchema(Schema):
    """Schema for serializing a driver in responses."""

    id = fields.String(dump_only=True)
    user_id = fields.String(dump_only=True)
    vehicle_type = fields.String(dump_only=True)
    vehicle_number = fields.String(dump_only=True)
    license_number = fields.String(dump_only=True)
    operating_area = fields.Method("get_operating_area", dump_only=True)
    is_available = fields.Boolean(dump_only=True)
    average_rating = fields.Float(dump_only=True)
    total_assignments = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_operating_area(self, obj):
        """Serialize OperatingArea enum to its string value."""
        if obj.operating_area:
            return obj.operating_area.value
        return None


class BookingDriverResponseSchema(Schema):
    """Schema for serializing a booking-driver assignment."""

    id = fields.String(dump_only=True)
    booking_id = fields.String(dump_only=True)
    driver_id = fields.String(dump_only=True)
    assigned_at = fields.DateTime(dump_only=True)
    assigned_by = fields.String(dump_only=True)
