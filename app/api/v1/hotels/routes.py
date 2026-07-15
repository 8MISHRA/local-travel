"""Hotel routes: CRUD for hotels, room types, and availability.

Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
- 8.1: POST /hotels (admin) registers hotel with partner association
- 8.2: POST /hotels/{id}/room-types creates room type for hotel
- 8.3: POST /hotels/{id}/availability sets room availability
- 8.4: GET /hotels/availability queries available hotels for destination/dates
- 8.5: Reject past dates in availability setting (HTTP 422)
"""

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.hotels.schemas import (
    AvailabilityQuerySchema,
    AvailabilityResultSchema,
    CreateHotelSchema,
    CreateRoomTypeSchema,
    HotelDetailResponseSchema,
    HotelResponseSchema,
    RoomAvailabilityResponseSchema,
    RoomTypeResponseSchema,
    SetAvailabilitySchema,
    UpdateHotelSchema,
    UpdateRoomTypeSchema,
)
from app.middleware.auth_middleware import auth_required
from app.middleware.rbac_middleware import ADMIN_ROLES, PARTNER_ROLES
from app.services.hotel_service import HotelService
from app.utils.exceptions import AppError
from app.utils.pagination import get_pagination_params
from app.utils.response import error_response, paginated_response, success_response

hotels_bp = Blueprint("hotels", __name__, url_prefix="/hotels")


@hotels_bp.route("", methods=["GET"])
def list_hotels():
    """List all active hotels with pagination.

    Public endpoint - no authentication required.
    Query params: page, per_page, sort_by, destination_id
    """
    pagination = get_pagination_params()
    filters = {}

    destination_id = request.args.get("destination_id")
    if destination_id:
        filters["destination_id"] = destination_id

    is_active = request.args.get("is_active")
    if is_active is not None:
        filters["is_active"] = is_active.lower() == "true"

    sort_by_raw = request.args.get("sort_by")

    service = HotelService()
    items, pagination_meta = service.list_hotels(
        page=pagination["page"],
        per_page=pagination["per_page"],
        filters=filters if filters else None,
        sort_by=sort_by_raw,
    )

    schema = HotelResponseSchema()
    return paginated_response(
        items=items,
        total=pagination_meta["total"],
        page=pagination_meta["page"],
        per_page=pagination_meta["per_page"],
        schema=schema,
    )


@hotels_bp.route("/<string:hotel_id>", methods=["GET"])
def get_hotel(hotel_id):
    """Get a hotel by ID with its room types.

    Public endpoint - no authentication required.

    Args:
        hotel_id: UUID of the hotel.
    """
    service = HotelService()

    try:
        hotel = service.get_hotel(hotel_id)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    # Load room types for the detail view
    room_types = hotel.room_types.all()
    schema = HotelResponseSchema()
    hotel_data = schema.dump(hotel)

    room_type_schema = RoomTypeResponseSchema(many=True)
    hotel_data["room_types"] = room_type_schema.dump(room_types)

    return success_response(hotel_data, message="Hotel retrieved successfully.")


@hotels_bp.route("", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def create_hotel():
    """Register a new hotel.

    Admin-only endpoint.
    Request body: {partner_user_id, name, address, destination_id, star_rating, ...}
    Success: 201 with created hotel data.
    Errors: 422 (validation)
    """
    schema = CreateHotelSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = HotelService()

    try:
        hotel = service.register_hotel(
            partner_user_id=data["partner_user_id"],
            name=data["name"],
            address=data["address"],
            destination_id=data["destination_id"],
            star_rating=data["star_rating"],
            amenities=data.get("amenities"),
            contact_email=data.get("contact_email"),
            contact_phone=data.get("contact_phone"),
            description=data.get("description"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = HotelResponseSchema()
    return success_response(
        response_schema.dump(hotel),
        message="Hotel registered successfully.",
        status_code=201,
    )


@hotels_bp.route("/<string:hotel_id>", methods=["PUT"])
@auth_required(roles=PARTNER_ROLES)
def update_hotel(hotel_id):
    """Update a hotel.

    Admin or hotel partner endpoint.
    Request body: {name?, address?, star_rating?, amenities?, ...}
    Success: 200 with updated hotel data.
    Errors: 404 (not found), 422 (validation)
    """
    schema = UpdateHotelSchema()
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

    service = HotelService()

    try:
        hotel = service.update_hotel(hotel_id, **data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = HotelResponseSchema()
    return success_response(
        response_schema.dump(hotel),
        message="Hotel updated successfully.",
    )


@hotels_bp.route("/<string:hotel_id>/room-types", methods=["POST"])
@auth_required(roles=PARTNER_ROLES)
def create_room_type(hotel_id):
    """Add a room type to a hotel.

    Admin or hotel partner endpoint.
    Request body: {name, capacity, base_price, description?, amenities?}
    Success: 201 with created room type data.
    Errors: 404 (hotel not found), 422 (validation)
    """
    schema = CreateRoomTypeSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = HotelService()

    try:
        room_type = service.add_room_type(
            hotel_id=hotel_id,
            name=data["name"],
            capacity=data["capacity"],
            base_price=data["base_price"],
            description=data.get("description"),
            amenities=data.get("amenities"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = RoomTypeResponseSchema()
    return success_response(
        response_schema.dump(room_type),
        message="Room type created successfully.",
        status_code=201,
    )


@hotels_bp.route("/<string:hotel_id>/room-types/<string:room_type_id>", methods=["PUT"])
@auth_required(roles=PARTNER_ROLES)
def update_room_type(hotel_id, room_type_id):
    """Update a room type for a hotel.

    Admin or hotel partner endpoint.
    Request body: {name?, capacity?, base_price?, description?, amenities?}
    Success: 200 with updated room type data.
    Errors: 404 (not found), 422 (validation)
    """
    schema = UpdateRoomTypeSchema()
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

    service = HotelService()

    try:
        room_type = service.update_room_type(hotel_id, room_type_id, **data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = RoomTypeResponseSchema()
    return success_response(
        response_schema.dump(room_type),
        message="Room type updated successfully.",
    )


@hotels_bp.route("/<string:hotel_id>/availability", methods=["POST"])
@auth_required(roles=PARTNER_ROLES)
def set_availability(hotel_id):
    """Set room availability for a hotel.

    Admin or hotel partner endpoint.
    Rejects past dates with HTTP 422 (Requirement 8.5).
    Request body: {room_type_id, availability: [{date, available_count}, ...]}
    Success: 200 with availability data.
    Errors: 404 (not found), 422 (validation / past dates)
    """
    schema = SetAvailabilitySchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = HotelService()

    try:
        results = service.set_availability(
            hotel_id=hotel_id,
            room_type_id=data["room_type_id"],
            dates_availability=data["availability"],
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = RoomAvailabilityResponseSchema(many=True)
    return success_response(
        response_schema.dump(results),
        message="Availability updated successfully.",
    )


@hotels_bp.route("/availability", methods=["GET"])
def query_availability():
    """Query hotel availability by destination, date range, and room capacity.

    Public endpoint - no authentication required.
    Query params: destination_id (required), check_in (required), check_out (required),
                  min_capacity (optional, default 1), page, per_page
    """
    schema = AvailabilityQuerySchema()
    try:
        data = schema.load(request.args)
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = HotelService()

    try:
        results, pagination_meta = service.query_availability(
            destination_id=data["destination_id"],
            check_in=data["check_in"],
            check_out=data["check_out"],
            min_capacity=data["min_capacity"],
            page=data["page"],
            per_page=data["per_page"],
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    # Serialize results (list of (Hotel, RoomType) tuples)
    hotel_schema = HotelResponseSchema()
    room_type_schema = RoomTypeResponseSchema()
    serialized = [
        {
            "hotel": hotel_schema.dump(hotel),
            "room_type": room_type_schema.dump(room_type),
        }
        for hotel, room_type in results
    ]

    from flask import jsonify
    return jsonify({
        "success": True,
        "data": serialized,
        "pagination": pagination_meta,
        "message": "Availability retrieved successfully.",
    }), 200
