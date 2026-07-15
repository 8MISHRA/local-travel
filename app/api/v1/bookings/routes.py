"""Booking routes: multi-step booking flow and management endpoints.

Validates: Requirements 7.1, 7.2, 7.3, 7.5, 7.6, 7.7
- 7.1: POST /bookings creates a draft booking (customer)
- 7.2: POST /bookings/{id}/submit transitions to pending_payment
- 7.3: Payment confirmation handled by payment service (not in this module)
- 7.5: POST /bookings/{id}/cancel cancels a booking (customer)
- 7.6: PATCH /bookings/{id}/status admin/scout status update with timestamp
- 7.7: GET /bookings customer-scoped listing with pagination and status filtering
"""

from flask import Blueprint, g, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.bookings.schemas import (
    BookingCreateSchema,
    BookingListSchema,
    BookingResponseSchema,
    BookingStatusSchema,
    BookingUpdateSchema,
)
from app.middleware.auth_middleware import auth_required
from app.middleware.rbac_middleware import ADMIN_ROLES, STAFF_ROLES, is_admin
from app.models.booking import BookingStatus
from app.services.booking_service import BookingService
from app.utils.exceptions import AppError
from app.utils.response import error_response, paginated_response, success_response

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")


@bookings_bp.route("", methods=["GET"])
@auth_required()
def list_bookings():
    """List bookings with pagination and optional status filter.

    Customer users see only their own bookings.
    Admin/super_admin users see all bookings (customer_id filter optional).

    Query parameters:
        page (int): Page number (default 1)
        per_page (int): Items per page (default 20, max 100)
        status (str): Filter by booking status

    Returns:
        Paginated list of bookings.
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    status_filter = request.args.get("status")

    # Validate status filter if provided
    status_enum = None
    if status_filter:
        try:
            status_enum = BookingStatus(status_filter)
        except ValueError:
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid status filter: '{status_filter}'.",
                details={"valid_statuses": [s.value for s in BookingStatus]},
                status_code=422,
            )

    service = BookingService()

    # Admin sees all bookings (or filtered by customer_id); customer sees only their own
    if is_admin():
        customer_id = request.args.get("customer_id")  # None means all bookings
        items, pagination_meta = service.list_for_customer(
            customer_id=customer_id,
            page=page,
            per_page=per_page,
            status=status_enum,
        )
    else:
        items, pagination_meta = service.list_for_customer(
            customer_id=g.current_user_id,
            page=page,
            per_page=per_page,
            status=status_enum,
        )

    schema = BookingListSchema()
    return paginated_response(
        items=items,
        total=pagination_meta["total"],
        page=pagination_meta["page"],
        per_page=pagination_meta["per_page"],
        schema=schema,
    )


@bookings_bp.route("/<string:booking_id>", methods=["GET"])
@auth_required()
def get_booking(booking_id):
    """Get a single booking by ID.

    Customers can only view their own bookings.
    Admin/super_admin can view any booking.

    Args:
        booking_id: UUID of the booking.

    Returns:
        Full booking data.
    """
    service = BookingService()

    try:
        booking = service.repo.get_by_id(booking_id)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    if booking is None:
        return error_response(
            "NOT_FOUND",
            f"Booking with id '{booking_id}' not found.",
            status_code=404,
        )

    # Authorization: customers can only see their own bookings
    if not is_admin() and booking.customer_id != g.current_user_id:
        return error_response(
            "FORBIDDEN",
            "You do not have permission to view this booking.",
            status_code=403,
        )

    schema = BookingResponseSchema()
    return success_response(
        schema.dump(booking),
        message="Booking retrieved successfully.",
    )


@bookings_bp.route("", methods=["POST"])
@auth_required(roles=["customer", "admin", "super_admin"])
def create_booking():
    """Create a new draft booking.

    Customer creates a booking by selecting a package, dates, and traveller info.

    Request body:
        package_id (str): UUID of the selected package
        travel_start_date (date): Start date (YYYY-MM-DD)
        travel_end_date (date): End date (YYYY-MM-DD)
        num_travellers (int): Number of travellers
        traveller_type (str): Type of traveller group
        special_requests (str, optional): Special requests text

    Returns:
        201 with created booking data.
    """
    schema = BookingCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = BookingService()

    try:
        booking = service.create_draft(
            customer_id=g.current_user_id,
            package_id=data["package_id"],
            travel_start_date=data["travel_start_date"],
            travel_end_date=data["travel_end_date"],
            num_travellers=data["num_travellers"],
            traveller_type=data["traveller_type"],
        )

        # Set special_requests if provided
        if data.get("special_requests"):
            booking.special_requests = data["special_requests"]
            service.session.commit()

    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = BookingResponseSchema()
    return success_response(
        response_schema.dump(booking),
        message="Booking created successfully.",
        status_code=201,
    )


@bookings_bp.route("/<string:booking_id>", methods=["PATCH"])
@auth_required(roles=["customer", "admin", "super_admin"])
def update_booking(booking_id):
    """Update a draft booking's details.

    Customers can update their own draft bookings (hotel, transport, add-ons).
    Admin can update any draft booking.

    Args:
        booking_id: UUID of the booking to update.

    Request body:
        hotel_preference_id (str, optional)
        room_type_id (str, optional)
        transport_preferences (dict, optional)
        add_ons (list, optional)
        special_requests (str, optional)
        num_travellers (int, optional)
        traveller_type (str, optional)

    Returns:
        200 with updated booking data.
    """
    schema = BookingUpdateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = BookingService()

    # Fetch the booking
    booking = service.repo.get_by_id(booking_id)
    if booking is None:
        return error_response(
            "NOT_FOUND",
            f"Booking with id '{booking_id}' not found.",
            status_code=404,
        )

    # Authorization: customers can only update their own bookings
    if not is_admin() and booking.customer_id != g.current_user_id:
        return error_response(
            "FORBIDDEN",
            "You do not have permission to update this booking.",
            status_code=403,
        )

    # Only allow updates on draft bookings
    if booking.status != BookingStatus.draft:
        return error_response(
            "INVALID_STATE_TRANSITION",
            "Only draft bookings can be updated.",
            details={"current_status": booking.status.value},
            status_code=422,
        )

    # Apply updates
    updatable_fields = [
        "hotel_preference_id",
        "room_type_id",
        "transport_preferences",
        "add_ons",
        "special_requests",
        "num_travellers",
        "traveller_type",
    ]
    for field in updatable_fields:
        if field in data and data[field] is not None:
            setattr(booking, field, data[field])

    service.session.commit()

    response_schema = BookingResponseSchema()
    return success_response(
        response_schema.dump(booking),
        message="Booking updated successfully.",
    )


@bookings_bp.route("/<string:booking_id>/submit", methods=["POST"])
@auth_required(roles=["customer", "admin", "super_admin"])
def submit_booking(booking_id):
    """Submit a draft booking, transitioning it to pending_payment.

    Calculates pricing and moves the booking from draft to pending_payment.
    Customers can only submit their own bookings.

    Args:
        booking_id: UUID of the booking to submit.

    Returns:
        200 with updated booking data including calculated pricing.
    """
    service = BookingService()

    # Fetch the booking to check ownership
    booking = service.repo.get_by_id(booking_id)
    if booking is None:
        return error_response(
            "NOT_FOUND",
            f"Booking with id '{booking_id}' not found.",
            status_code=404,
        )

    # Authorization: customers can only submit their own bookings
    if not is_admin() and booking.customer_id != g.current_user_id:
        return error_response(
            "FORBIDDEN",
            "You do not have permission to submit this booking.",
            status_code=403,
        )

    try:
        booking = service.submit_details(
            booking_id=booking_id,
            hotel_preference_id=booking.hotel_preference_id,
            room_type_id=booking.room_type_id,
            transport_preferences=booking.transport_preferences,
            add_ons=booking.add_ons,
            changed_by=g.current_user_id,
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = BookingResponseSchema()
    return success_response(
        response_schema.dump(booking),
        message="Booking submitted successfully. Awaiting payment.",
    )


@bookings_bp.route("/<string:booking_id>/cancel", methods=["POST"])
@auth_required(roles=["customer", "admin", "super_admin"])
def cancel_booking(booking_id):
    """Cancel a booking.

    Customers can cancel their own bookings (from pending_payment or confirmed).
    Admin can cancel any booking.

    Args:
        booking_id: UUID of the booking to cancel.

    Returns:
        200 with updated booking data.
    """
    service = BookingService()

    # Fetch the booking to check ownership
    booking = service.repo.get_by_id(booking_id)
    if booking is None:
        return error_response(
            "NOT_FOUND",
            f"Booking with id '{booking_id}' not found.",
            status_code=404,
        )

    # Authorization: customers can only cancel their own bookings
    if not is_admin() and booking.customer_id != g.current_user_id:
        return error_response(
            "FORBIDDEN",
            "You do not have permission to cancel this booking.",
            status_code=403,
        )

    # Parse optional notes from request body
    body = request.get_json(silent=True) or {}
    notes = body.get("notes")

    try:
        booking, initiate_refund = service.cancel(
            booking_id=booking_id,
            changed_by=g.current_user_id,
            notes=notes,
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = BookingResponseSchema()
    response_data = response_schema.dump(booking)
    response_data["refund_initiated"] = initiate_refund

    return success_response(
        response_data,
        message="Booking cancelled successfully.",
    )


@bookings_bp.route("/<string:booking_id>/status", methods=["PATCH"])
@auth_required(roles=STAFF_ROLES)
def update_booking_status(booking_id):
    """Update a booking's status (admin/scout only).

    Allows admin and scout users to transition a booking to any valid next status.
    Records the status change with timestamp and acting user.

    Args:
        booking_id: UUID of the booking.

    Request body:
        status (str): Target booking status
        notes (str, optional): Notes about the status change

    Returns:
        200 with updated booking data.
    """
    schema = BookingStatusSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    target_status = BookingStatus(data["status"])

    service = BookingService()

    try:
        booking = service.update_status(
            booking_id=booking_id,
            target_status=target_status,
            changed_by=g.current_user_id,
            notes=data.get("notes"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = BookingResponseSchema()
    return success_response(
        response_schema.dump(booking),
        message="Booking status updated successfully.",
    )
