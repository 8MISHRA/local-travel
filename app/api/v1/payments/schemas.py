"""Payment request/response schemas for validation and serialization.

Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 26.1
- 11.1: Payment initiation with amount, currency, method
- 11.2: Payment callback processing
- 11.3: Payment failure handling
- 11.4: Partial payment tracking
- 11.5: Refund initiation
- 26.1: Schema-based input validation via Marshmallow
"""

from marshmallow import Schema, fields, validate

from app.models.payment import PaymentStatus, RefundStatus

# Valid payment statuses for callback
VALID_CALLBACK_STATUSES = ["completed", "failed"]

# Valid payment methods
VALID_PAYMENT_METHODS = ["card", "upi", "net_banking", "wallet", "cod"]


# --- Request Schemas ---


class PaymentInitiateSchema(Schema):
    """Schema for initiating a payment.

    Required: booking_id, amount
    Optional: currency, payment_method
    """

    booking_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=36),
        error_messages={"required": "Booking ID is required."},
    )
    amount = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, error="Amount must be greater than zero."),
        error_messages={"required": "Amount is required."},
    )
    currency = fields.String(
        required=False,
        load_default="INR",
        validate=validate.Length(min=3, max=3),
    )
    payment_method = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(
            VALID_PAYMENT_METHODS,
            error="Payment method must be one of: {choices}.",
        ),
    )


class PaymentCallbackSchema(Schema):
    """Schema for processing a payment gateway callback.

    Required: payment_id, status
    Optional: gateway_transaction_id, gateway_response
    """

    payment_id = fields.String(
        required=True,
        validate=validate.Length(min=1, max=36),
        error_messages={"required": "Payment ID is required."},
    )
    status = fields.String(
        required=True,
        validate=validate.OneOf(
            VALID_CALLBACK_STATUSES,
            error="Status must be one of: {choices}.",
        ),
        error_messages={"required": "Status is required."},
    )
    gateway_transaction_id = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    gateway_response = fields.Dict(
        required=False,
        load_default=None,
        allow_none=True,
    )


class RefundInitiateSchema(Schema):
    """Schema for initiating a refund.

    Optional: amount (defaults to full payment amount), reason
    """

    amount = fields.Float(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=0.01, error="Refund amount must be greater than zero."),
    )
    reason = fields.String(
        required=False,
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=1000),
    )


# --- Response Schemas ---


class PaymentResponseSchema(Schema):
    """Schema for serializing payment data in responses."""

    id = fields.String(dump_only=True)
    booking_id = fields.String(dump_only=True)
    amount = fields.Float(dump_only=True)
    currency = fields.String(dump_only=True)
    payment_method = fields.String(dump_only=True, allow_none=True)
    gateway_transaction_id = fields.String(dump_only=True, allow_none=True)
    status = fields.Method("get_status")
    gateway_response = fields.Dict(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):
        """Serialize payment status enum to its string value."""
        if obj.status:
            return obj.status.value if hasattr(obj.status, "value") else str(obj.status)
        return None


class RefundResponseSchema(Schema):
    """Schema for serializing refund data in responses."""

    id = fields.String(dump_only=True)
    payment_id = fields.String(dump_only=True)
    booking_id = fields.String(dump_only=True)
    amount = fields.Float(dump_only=True)
    reason = fields.String(dump_only=True, allow_none=True)
    status = fields.Method("get_status")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):
        """Serialize refund status enum to its string value."""
        if obj.status:
            return obj.status.value if hasattr(obj.status, "value") else str(obj.status)
        return None


class PaymentListSchema(Schema):
    """Schema for serializing payments in list responses."""

    id = fields.String(dump_only=True)
    booking_id = fields.String(dump_only=True)
    amount = fields.Float(dump_only=True)
    currency = fields.String(dump_only=True)
    payment_method = fields.String(dump_only=True, allow_none=True)
    status = fields.Method("get_status")
    created_at = fields.DateTime(dump_only=True)

    def get_status(self, obj):
        """Serialize payment status enum to its string value."""
        if obj.status:
            return obj.status.value if hasattr(obj.status, "value") else str(obj.status)
        return None
