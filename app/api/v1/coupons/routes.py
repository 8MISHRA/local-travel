"""Coupon routes - MVP Stub.

This module will implement coupon CRUD, validation, and application endpoints.
TODO: Implement in next iteration.

Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

coupons_bp = Blueprint("coupons", __name__, url_prefix="/coupons")


@coupons_bp.route("", methods=["GET"])
def list_coupons():
    """List coupons - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Coupon endpoints coming soon.", status_code=501)


@coupons_bp.route("", methods=["POST"])
def create_coupon():
    """Create a coupon - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Coupon endpoints coming soon.", status_code=501)


@coupons_bp.route("/validate", methods=["POST"])
def validate_coupon():
    """Validate a coupon code - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Coupon endpoints coming soon.", status_code=501)
