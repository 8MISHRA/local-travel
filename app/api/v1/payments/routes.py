"""Payment routes: initiation, callback, listing, and refunds.

Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5
- 11.1: POST /payments (customer) initiates payment with pending status
- 11.2: POST /payments/callback (webhook, no auth) processes gateway callback
- 11.3: Payment failure handled in callback (status=failed)
- 11.4: GET /bookings/{id}/payments lists partial payments for a booking
- 11.5: POST /payments/{id}/refund (admin) initiates refund
"""

from flask import Blueprint, g, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.payments.schemas import (
    PaymentCallbackSchema,
    PaymentInitiateSchema,
    PaymentListSchema,
    PaymentResponseSchema,
    RefundInitiateSchema,
    RefundResponseSchema,
)
from app.middleware.auth_middleware import auth_required
from app.middleware.rbac_middleware import ADMIN_ROLES
from app.services.payment_service import PaymentService
from app.utils.exceptions import AppError
from app.utils.pagination import get_pagination_params
from app.utils.response import error_response, success_response

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")
bookings_payments_bp = Blueprint("bookings_payments", __name__, url_prefix="/bookings")


@payments_bp.route("", methods=["POST"])
@auth_required(roles=["customer", "admin", "super_admin"])
def initiate_payment():
    """Initiate a payment for a booking.

    Creates a payment record with status=pending.
    Request body: {booking_id, amount, currency?, payment_method?}
    Success: 201 with created payment data.
    Errors: 404 (booking not found), 422 (validation)
    """
    schema = PaymentInitiateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = PaymentService()

    try:
        payment = service.initiate_payment(
            booking_id=data["booking_id"],
            amount=data["amount"],
            currency=data.get("currency", "INR"),
            payment_method=data.get("payment_method"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = PaymentResponseSchema()
    return success_response(
        response_schema.dump(payment),
        message="Payment initiated successfully.",
        status_code=201,
    )


@payments_bp.route("/callback", methods=["POST"])
def payment_callback():
    """Process a payment gateway callback (webhook).

    No authentication required — called by the payment gateway.
    Request body: {payment_id, status, gateway_transaction_id?, gateway_response?}
    Success: 200 with updated payment data.
    Errors: 404 (payment not found), 422 (validation)
    """
    schema = PaymentCallbackSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = PaymentService()

    try:
        payment = service.process_callback(
            payment_id=data["payment_id"],
            status=data["status"],
            gateway_transaction_id=data.get("gateway_transaction_id"),
            gateway_response=data.get("gateway_response"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = PaymentResponseSchema()
    return success_response(
        response_schema.dump(payment),
        message="Payment callback processed successfully.",
    )


@payments_bp.route("/<string:payment_id>/refund", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def initiate_refund(payment_id):
    """Initiate a refund for a completed payment.

    Admin-only endpoint.
    Request body: {amount?, reason?}
    Success: 201 with refund data.
    Errors: 404 (payment not found), 422 (validation - not completed, amount exceeds)
    """
    schema = RefundInitiateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = PaymentService()

    try:
        refund = service.initiate_refund(
            payment_id=payment_id,
            amount=data.get("amount"),
            reason=data.get("reason"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = RefundResponseSchema()
    return success_response(
        response_schema.dump(refund),
        message="Refund initiated successfully.",
        status_code=201,
    )


@bookings_payments_bp.route("/<string:booking_id>/payments", methods=["GET"])
@auth_required(roles=["customer", "admin", "super_admin"])
def list_booking_payments(booking_id):
    """List all payments for a booking.

    Returns paginated payments with total paid amount for partial payment tracking.
    Query params: page, per_page
    Success: 200 with payment list + pagination + total_paid.
    Errors: 404 (booking not found)
    """
    pagination = get_pagination_params()

    service = PaymentService()

    try:
        items, pagination_meta, total_paid = service.list_for_booking(
            booking_id=booking_id,
            page=pagination["page"],
            per_page=pagination["per_page"],
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    schema = PaymentListSchema()
    from flask import jsonify

    return jsonify({
        "success": True,
        "data": schema.dump(items, many=True),
        "pagination": pagination_meta,
        "total_paid": str(total_paid),
        "message": "Success",
    }), 200
