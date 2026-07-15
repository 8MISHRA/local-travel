"""Review routes - MVP Stub.

This module will implement review submission, moderation, and listing endpoints.
TODO: Implement in next iteration.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

reviews_bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews_bp.route("", methods=["GET"])
def list_reviews():
    """List reviews - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Review endpoints coming soon.", status_code=501)


@reviews_bp.route("", methods=["POST"])
def create_review():
    """Submit a review - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Review endpoints coming soon.", status_code=501)


@reviews_bp.route("/<string:review_id>/moderate", methods=["PATCH"])
def moderate_review(review_id):
    """Moderate a review - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Review endpoints coming soon.", status_code=501)
