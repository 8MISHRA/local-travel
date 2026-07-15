"""Destination request/response schemas for validation and serialization.

Validates: Requirements 6.1, 6.2, 6.3, 26.1
- 6.1: Destination fields (name, description, is_primary)
- 6.2: Sub-destination fields (name, description, coordinates, category, media)
- 6.3: Hierarchical response structure
- 26.1: Schema-based validation via Marshmallow
"""

from marshmallow import Schema, fields, validate

from app.models.destination import SubDestinationCategory


# --- Valid category values for validation ---
VALID_CATEGORIES = [c.value for c in SubDestinationCategory]


# --- Request Schemas ---


class CreateDestinationSchema(Schema):
    """Schema for creating a destination.

    Required: name
    Optional: description, is_primary
    """

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters."),
        error_messages={"required": "Name is required."},
    )
    description = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=5000, error="Description must not exceed 5000 characters."),
    )
    is_primary = fields.Boolean(
        required=False,
        load_default=False,
    )


class UpdateDestinationSchema(Schema):
    """Schema for updating a destination.

    All fields optional.
    """

    name = fields.String(
        required=False,
        validate=validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters."),
    )
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=5000, error="Description must not exceed 5000 characters."),
    )
    is_primary = fields.Boolean(required=False)


class CreateSubDestinationSchema(Schema):
    """Schema for creating a sub-destination.

    Required: name, category
    Optional: description, latitude, longitude, media_urls
    """

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=150, error="Name must be between 1 and 150 characters."),
        error_messages={"required": "Name is required."},
    )
    category = fields.String(
        required=True,
        validate=validate.OneOf(
            VALID_CATEGORIES,
            error="Category must be one of: {choices}.",
        ),
        error_messages={"required": "Category is required."},
    )
    description = fields.String(
        required=False,
        load_default=None,
        validate=validate.Length(max=5000, error="Description must not exceed 5000 characters."),
    )
    latitude = fields.Float(
        required=False,
        load_default=None,
        validate=validate.Range(min=-90, max=90, error="Latitude must be between -90 and 90."),
    )
    longitude = fields.Float(
        required=False,
        load_default=None,
        validate=validate.Range(min=-180, max=180, error="Longitude must be between -180 and 180."),
    )
    media_urls = fields.List(
        fields.String(validate=validate.Length(max=500)),
        required=False,
        load_default=None,
    )


# --- Response Schemas ---


class SubDestinationResponseSchema(Schema):
    """Schema for serializing a sub-destination in responses."""

    id = fields.String(dump_only=True)
    destination_id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    latitude = fields.Float(dump_only=True)
    longitude = fields.Float(dump_only=True)
    category = fields.Method("get_category")
    media_urls = fields.List(fields.String(), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_category(self, obj):
        """Serialize category enum to its string value."""
        if obj.category:
            return obj.category.value
        return None


class DestinationResponseSchema(Schema):
    """Schema for serializing a destination in responses."""

    id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    is_primary = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class DestinationHierarchicalSchema(Schema):
    """Schema for serializing a destination with nested sub-destinations."""

    id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    is_primary = fields.Boolean(dump_only=True)
    sub_destinations = fields.List(
        fields.Nested(SubDestinationResponseSchema),
        dump_only=True,
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
