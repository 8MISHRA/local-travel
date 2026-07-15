"""Wishlist routes - MVP Stub.

This module will implement wishlist add, remove, and listing endpoints.
TODO: Implement in next iteration.

Requirements: 18.1, 18.2, 18.3, 18.4
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

wishlist_bp = Blueprint("wishlist", __name__, url_prefix="/wishlist")


@wishlist_bp.route("", methods=["GET"])
def list_wishlist():
    """List wishlist items - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Wishlist endpoints coming soon.", status_code=501)


@wishlist_bp.route("", methods=["POST"])
def add_to_wishlist():
    """Add to wishlist - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Wishlist endpoints coming soon.", status_code=501)


@wishlist_bp.route("/<string:package_id>", methods=["DELETE"])
def remove_from_wishlist(package_id):
    """Remove from wishlist - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Wishlist endpoints coming soon.", status_code=501)
