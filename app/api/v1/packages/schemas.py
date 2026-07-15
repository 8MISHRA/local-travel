"""Package request/response schemas for validation and serialization.

Validates: Requirements 5.1, 5.2, 5.3, 5.5, 5.6, 26.1
- 5.1: Package creation with title, description, destination, duration, pricing, itinerary
- 5.2: Package listing response
- 5.3: Package update fields
- 5.5: Pricing tier schema
- 5.6: Itinerary schema
- 26.1: Schema-based input validation via Marshmallow
"""

from marshmallow import Schema, fields, validate

from app.models.package import TravellerType

# Valid traveller type values for validation
VALID_TRAVELLER_TYPES = [t.value for t in TravellerType]


# --- Nested Schemas ---


class PricingTierSchema(Schema):
    """Schema for pricing tier input/output.

    Required: tier_name, price
    Optional: max_persons, description
    """

    id = fields.String(dump_only=True)
    package_id = fields.String(dump_only=True)
    tier_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50, error="Tier name must be between 1 and 50 characters."),
        error_messages={"required": "Tier name is required."},
    )
    price = fields.Float(
        required=True,
        validate=validate.Range(min=0, error="Price must be a non-negative number."),
        error_messages={"required": "Price is required."},
    )
    max_persons = fields.Integer(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="Max persons must be at least 1."),
    )
    description = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255, error="Description must not exceed 255 characters."),
    )


class ItinerarySchema(Schema):
    """Schema for itinerary day input/output.

    Required: day_number, title, description
    Optional: activities
    """

    id = fields.String(dump_only=True)
    package_id = fields.String(dump_only=True)
    day_number = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Day number must be at least 1."),
        error_messages={"required": "Day number is required."},
    )
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error="Title must be between 1 and 255 characters."),
        error_messages={"required": "Title is required."},
    )
    description = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Description is required."),
        error_messages={"required": "Description is required."},
    )
    activities = fields.List(
        fields.String(),
        required=False,
        load_default=[],
    )


# --- Request Schemas ---


class PackageCreateSchema(Schema):
    """Schema for package creation requests.

    Required: title, description, destination_id, duration_days, duration_nights,
              traveller_type, inclusions, exclusions
    Optional: featured_image_url, is_active, pricing_tiers, itineraries
    """

    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255, error="Title must be between 1 and 255 characters."),
        error_messages={"required": "Title is required."},
    )
    description = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Description is required."),
        error_messages={"required": "Description is required."},
    )
    destination_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=36, error="Destination ID is required."),
        error_messages={"required": "Destination ID is required."},
    )
    duration_days = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="Duration days must be at least 1."),
        error_messages={"required": "Duration days is required."},
    )
    duration_nights = fields.Integer(
        required=True,
        validate=validate.Range(min=0, error="Duration nights must be non-negative."),
        error_messages={"required": "Duration nights is required."},
    )
    traveller_type = fields.String(
        required=True,
        validate=validate.OneOf(
            VALID_TRAVELLER_TYPES,
            error="Traveller type must be one of: {choices}.",
        ),
        error_messages={"required": "Traveller type is required."},
    )
    inclusions = fields.List(
        fields.String(),
        required=True,
        error_messages={"required": "Inclusions is required."},
    )
    exclusions = fields.List(
        fields.String(),
        required=True,
        error_messages={"required": "Exclusions is required."},
    )
    featured_image_url = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=500, error="Featured image URL must not exceed 500 characters."),
    )
    is_active = fields.Boolean(
        required=False,
        load_default=True,
    )
    pricing_tiers = fields.List(
        fields.Nested(PricingTierSchema),
        required=False,
        load_default=[],
    )
    itineraries = fields.List(
        fields.Nested(ItinerarySchema),
        required=False,
        load_default=[],
    )


class PackageUpdateSchema(Schema):
    """Schema for package update requests.

    All fields are optional. Only provided fields will be updated.
    """

    title = fields.String(
        required=False,
        validate=validate.Length(min=1, max=255, error="Title must be between 1 and 255 characters."),
    )
    description = fields.String(
        required=False,
        validate=validate.Length(min=1, error="Description cannot be empty."),
    )
    destination_id = fields.String(
        required=False,
        validate=validate.Length(min=1, max=36),
    )
    duration_days = fields.Integer(
        required=False,
        validate=validate.Range(min=1, error="Duration days must be at least 1."),
    )
    duration_nights = fields.Integer(
        required=False,
        validate=validate.Range(min=0, error="Duration nights must be non-negative."),
    )
    traveller_type = fields.String(
        required=False,
        validate=validate.OneOf(
            VALID_TRAVELLER_TYPES,
            error="Traveller type must be one of: {choices}.",
        ),
    )
    inclusions = fields.List(
        fields.String(),
        required=False,
    )
    exclusions = fields.List(
        fields.String(),
        required=False,
    )
    featured_image_url = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=500, error="Featured image URL must not exceed 500 characters."),
    )
    is_active = fields.Boolean(required=False)


# --- Response Schemas ---


class PricingTierResponseSchema(Schema):
    """Schema for serializing pricing tier data in responses."""

    id = fields.String(dump_only=True)
    package_id = fields.String(dump_only=True)
    tier_name = fields.String(dump_only=True)
    price = fields.Float(dump_only=True)
    max_persons = fields.Integer(dump_only=True)
    description = fields.String(dump_only=True)


class ItineraryResponseSchema(Schema):
    """Schema for serializing itinerary data in responses."""

    id = fields.String(dump_only=True)
    package_id = fields.String(dump_only=True)
    day_number = fields.Integer(dump_only=True)
    title = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    activities = fields.List(fields.String(), dump_only=True)


class PackageListSchema(Schema):
    """Schema for serializing packages in list responses (without nested details)."""

    id = fields.String(dump_only=True)
    title = fields.String(dump_only=True)
    slug = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    destination_id = fields.String(dump_only=True)
    duration_days = fields.Integer(dump_only=True)
    duration_nights = fields.Integer(dump_only=True)
    traveller_type = fields.Method("get_traveller_type")
    inclusions = fields.List(fields.String(), dump_only=True)
    exclusions = fields.List(fields.String(), dump_only=True)
    is_active = fields.Boolean(dump_only=True)
    featured_image_url = fields.String(dump_only=True)
    average_rating = fields.Float(dump_only=True)
    total_reviews = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_traveller_type(self, obj):
        """Serialize traveller_type enum to its string value."""
        if obj.traveller_type:
            return obj.traveller_type.value if hasattr(obj.traveller_type, "value") else str(obj.traveller_type)
        return None


class PackageDetailSchema(PackageListSchema):
    """Schema for serializing a single package with pricing tiers and itineraries."""

    pricing_tiers = fields.Method("get_pricing_tiers")
    itineraries = fields.Method("get_itineraries")

    def get_pricing_tiers(self, obj):
        """Serialize the package's pricing tiers."""
        schema = PricingTierResponseSchema(many=True)
        tiers = obj.pricing_tiers.all() if hasattr(obj.pricing_tiers, "all") else obj.pricing_tiers
        return schema.dump(tiers)

    def get_itineraries(self, obj):
        """Serialize the package's itineraries ordered by day number."""
        schema = ItineraryResponseSchema(many=True)
        from app.models.package import Itinerary
        itineraries = (
            obj.itineraries.order_by(Itinerary.day_number.asc()).all()
            if hasattr(obj.itineraries, "order_by")
            else obj.itineraries
        )
        return schema.dump(itineraries)
