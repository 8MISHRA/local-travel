"""Scout routes: CRUD for scouts, assignment to bookings, and ratings.

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
- 9.1: POST /scouts (admin) creates scout profile
- 9.2: POST /bookings/{id}/assign-scout (admin) assigns scout to booking
- 9.3: Updates scout availability and creates assignment record
- 9.4: POST /scouts/{id}/ratings (customer) submits rating
- 9.5: GET /scouts (admin) lists scouts with availability, rating, assignments
"""

from flask import Blueprint, request

from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.scouts.schemas import (
    AssignScoutSchema,
    BookingScoutResponseSchema,
    CreateScoutSchema,
    RateScoutSchema,
    ScoutRatingResponseSchema,
    ScoutResponseSchema,
    UpdateScoutSchema,
)
from app.middleware.auth_middleware import auth_required
from app.middleware.rbac_middleware import ADMIN_ROLES, ALL_AUTHENTICATED_ROLES
from app.services.scout_service import ScoutService
from app.utils.exceptions import AppError
from app.utils.pagination import get_pagination_params
from app.utils.response import error_response, paginated_response, success_response

from flask import g

scouts_bp = Blueprint("scouts", __name__, url_prefix="/scouts")


@scouts_bp.route("", methods=["GET"])
@auth_required(roles=ADMIN_ROLES)
def list_scouts():
    """List all scouts with pagination and filtering.

    Admin-only endpoint.
    Query params: page, per_page, sort_by, operating_area, is_available
    """
    pagination = get_pagination_params()
    filters = {}

    operating_area = request.args.get("operating_area")
    if operating_area:
        filters["operating_area"] = operating_area

    is_available = request.args.get("is_available")
    if is_available is not None:
        filters["is_available"] = is_available.lower() == "true"

    sort_by_raw = request.args.get("sort_by")

    service = ScoutService()
    items, pagination_meta = service.list_scouts(
        page=pagination["page"],
        per_page=pagination["per_page"],
        filters=filters if filters else None,
        sort_by=sort_by_raw,
    )

    schema = ScoutResponseSchema()
    return paginated_response(
        items=items,
        total=pagination_meta["total"],
        page=pagination_meta["page"],
        per_page=pagination_meta["per_page"],
        schema=schema,
    )


@scouts_bp.route("", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def create_scout():
    """Create a new scout profile.

    Admin-only endpoint.
    Request body: {user_id, languages, operating_area, specializations?, is_available?}
    Success: 201 with created scout data.
    Errors: 409 (duplicate), 422 (validation)
    """
    schema = CreateScoutSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = ScoutService()

    try:
        scout = service.create_scout(
            user_id=data["user_id"],
            languages=data["languages"],
            operating_area=data["operating_area"],
            specializations=data.get("specializations"),
            is_available=data.get("is_available", True),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = ScoutResponseSchema()
    return success_response(
        response_schema.dump(scout),
        message="Scout profile created successfully.",
        status_code=201,
    )


@scouts_bp.route("/<string:scout_id>", methods=["PUT"])
@auth_required(roles=ADMIN_ROLES)
def update_scout(scout_id):
    """Update a scout profile.

    Admin-only endpoint.
    Request body: {languages?, specializations?, operating_area?, is_available?}
    Success: 200 with updated scout data.
    Errors: 404 (not found), 422 (validation)
    """
    schema = UpdateScoutSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "No fields to update.",
            status_code=422,
        )

    service = ScoutService()

    try:
        scout = service.update_scout(scout_id, **data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = ScoutResponseSchema()
    return success_response(
        response_schema.dump(scout),
        message="Scout profile updated successfully.",
    )


@scouts_bp.route("/<string:scout_id>", methods=["GET"])
@auth_required(roles=ADMIN_ROLES)
def get_scout(scout_id):
    """Get a scout profile by ID.

    Admin-only endpoint.

    Args:
        scout_id: UUID of the scout.
    """
    service = ScoutService()

    try:
        scout = service.get_scout(scout_id)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = ScoutResponseSchema()
    return success_response(
        response_schema.dump(scout),
        message="Scout retrieved successfully.",
    )


# --- Booking assignment endpoint (nested under bookings for clarity) ---

bookings_scouts_bp = Blueprint("bookings_scouts", __name__, url_prefix="/bookings")


@bookings_scouts_bp.route("/<string:booking_id>/assign-scout", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def assign_scout_to_booking(booking_id):
    """Assign a scout to a booking.

    Admin-only endpoint.
    Request body: {scout_id}
    Success: 201 with assignment data.
    Errors: 404 (booking/scout not found), 409 (unavailable/already assigned), 422 (validation)
    """
    schema = AssignScoutSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = ScoutService()

    try:
        booking_scout = service.assign_to_booking(
            booking_id=booking_id,
            scout_id=data["scout_id"],
            assigned_by=g.current_user_id,
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = BookingScoutResponseSchema()
    return success_response(
        response_schema.dump(booking_scout),
        message="Scout assigned to booking successfully.",
        status_code=201,
    )


# --- Scout rating endpoint ---


@scouts_bp.route("/<string:scout_id>/ratings", methods=["POST"])
@auth_required(roles=ALL_AUTHENTICATED_ROLES)
def rate_scout(scout_id):
    """Submit a rating for a scout.

    Customer endpoint (any authenticated user can rate).
    Request body: {booking_id, rating, review_text?}
    Success: 201 with rating data.
    Errors: 404 (scout/booking not found), 422 (validation)
    """
    schema = RateScoutSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = ScoutService()

    try:
        review = service.rate_scout(
            scout_id=scout_id,
            customer_id=g.current_user_id,
            booking_id=data["booking_id"],
            rating=data["rating"],
            review_text=data.get("review_text"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = ScoutRatingResponseSchema()
    return success_response(
        response_schema.dump(review),
        message="Scout rating submitted successfully.",
        status_code=201,
    )
