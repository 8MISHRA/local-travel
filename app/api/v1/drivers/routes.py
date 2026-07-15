"""Driver routes: CRUD for drivers and assignment to bookings.

Validates: Requirements 10.1, 10.2, 10.3, 10.4
- 10.1: POST /drivers (admin) creates driver profile
- 10.2: POST /bookings/{id}/assign-driver (admin) assigns driver to booking
- 10.3: POST /drivers/{id}/ratings (customer) rates a driver
- 10.4: Return HTTP 409 if driver has overlapping assignment
"""

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.drivers.schemas import (
    AssignDriverSchema,
    BookingDriverResponseSchema,
    CreateDriverSchema,
    DriverResponseSchema,
    RateDriverSchema,
    UpdateDriverSchema,
)
from app.middleware.auth_middleware import auth_required
from app.middleware.rbac_middleware import ADMIN_ROLES
from app.models.scout import OperatingArea
from app.services.driver_service import DriverService
from app.utils.exceptions import AppError
from app.utils.pagination import get_pagination_params
from app.utils.response import error_response, paginated_response, success_response

drivers_bp = Blueprint("drivers", __name__, url_prefix="/drivers")


@drivers_bp.route("", methods=["GET"])
@auth_required(roles=ADMIN_ROLES)
def list_drivers():
    """List all drivers with pagination.

    Admin-only endpoint.
    Query params: page, per_page, sort_by, operating_area, is_available
    """
    pagination = get_pagination_params()
    filters = {}

    operating_area = request.args.get("operating_area")
    if operating_area:
        try:
            filters["operating_area"] = OperatingArea(operating_area)
        except ValueError:
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid operating area: '{operating_area}'. Must be 'varanasi' or 'mirzapur'.",
                status_code=422,
            )

    is_available = request.args.get("is_available")
    if is_available is not None:
        filters["is_available"] = is_available.lower() == "true"

    sort_by_raw = request.args.get("sort_by")

    service = DriverService()
    items, pagination_meta = service.list_drivers(
        page=pagination["page"],
        per_page=pagination["per_page"],
        filters=filters if filters else None,
        sort_by=sort_by_raw,
    )

    schema = DriverResponseSchema()
    return paginated_response(
        items=items,
        total=pagination_meta["total"],
        page=pagination_meta["page"],
        per_page=pagination_meta["per_page"],
        schema=schema,
    )


@drivers_bp.route("", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def create_driver():
    """Create a new driver profile.

    Admin-only endpoint.
    Request body: {user_id, vehicle_type, vehicle_number, license_number, operating_area}
    Success: 201 with created driver data.
    Errors: 409 (conflict - user already has driver profile), 422 (validation)
    """
    schema = CreateDriverSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    # Convert operating_area string to enum
    try:
        operating_area = OperatingArea(data["operating_area"])
    except ValueError:
        return error_response(
            "VALIDATION_ERROR",
            "Invalid operating area.",
            details={"operating_area": ["Must be 'varanasi' or 'mirzapur'."]},
            status_code=422,
        )

    service = DriverService()

    try:
        driver = service.create_driver(
            user_id=data["user_id"],
            vehicle_type=data["vehicle_type"],
            vehicle_number=data["vehicle_number"],
            license_number=data["license_number"],
            operating_area=operating_area,
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = DriverResponseSchema()
    return success_response(
        response_schema.dump(driver),
        message="Driver profile created successfully.",
        status_code=201,
    )


@drivers_bp.route("/<string:driver_id>", methods=["PUT"])
@auth_required(roles=ADMIN_ROLES)
def update_driver(driver_id):
    """Update a driver profile.

    Admin-only endpoint.
    Request body: {vehicle_type?, vehicle_number?, license_number?, operating_area?, is_available?}
    Success: 200 with updated driver data.
    Errors: 404 (not found), 422 (validation)
    """
    schema = UpdateDriverSchema()
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

    # Convert operating_area string to enum if provided
    if "operating_area" in data:
        try:
            data["operating_area"] = OperatingArea(data["operating_area"])
        except ValueError:
            return error_response(
                "VALIDATION_ERROR",
                "Invalid operating area.",
                details={"operating_area": ["Must be 'varanasi' or 'mirzapur'."]},
                status_code=422,
            )

    service = DriverService()

    try:
        driver = service.update_driver(driver_id, **data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = DriverResponseSchema()
    return success_response(
        response_schema.dump(driver),
        message="Driver profile updated successfully.",
    )


@drivers_bp.route("/<string:driver_id>/ratings", methods=["POST"])
@auth_required(roles=["customer", "admin", "super_admin"])
def rate_driver(driver_id):
    """Submit a rating for a driver.

    Customer endpoint (also accessible by admins).
    Request body: {rating (1-5), review_text?}
    Success: 200 with updated driver data.
    Errors: 404 (not found), 422 (validation)
    """
    schema = RateDriverSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = DriverService()

    try:
        driver = service.rate_driver(
            driver_id=driver_id,
            rating=data["rating"],
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = DriverResponseSchema()
    return success_response(
        response_schema.dump(driver),
        message="Driver rated successfully.",
    )


# --- Booking-scoped driver assignment endpoint ---
# This is registered on the bookings prefix via a separate blueprint

bookings_drivers_bp = Blueprint("bookings_drivers", __name__, url_prefix="/bookings")


@bookings_drivers_bp.route("/<string:booking_id>/assign-driver", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def assign_driver_to_booking(booking_id):
    """Assign a driver to a booking.

    Admin-only endpoint. Checks for scheduling conflicts before assignment.
    Request body: {driver_id}
    Success: 201 with booking-driver assignment data.
    Errors: 404 (booking/driver not found), 409 (scheduling conflict)
    """
    from flask import g

    schema = AssignDriverSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = DriverService()

    try:
        booking_driver = service.assign_to_booking(
            booking_id=booking_id,
            driver_id=data["driver_id"],
            assigned_by=g.current_user_id,
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = BookingDriverResponseSchema()
    return success_response(
        response_schema.dump(booking_driver),
        message="Driver assigned to booking successfully.",
        status_code=201,
    )
