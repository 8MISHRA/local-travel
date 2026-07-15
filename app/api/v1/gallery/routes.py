"""Gallery routes - MVP Stub.

This module will implement image upload, listing, deletion, and reordering endpoints.
TODO: Implement in next iteration.

Requirements: 14.1, 14.2, 14.3, 14.4
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

gallery_bp = Blueprint("gallery", __name__, url_prefix="/gallery")


@gallery_bp.route("", methods=["GET"])
def list_images():
    """List gallery images - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Gallery endpoints coming soon.", status_code=501)


@gallery_bp.route("", methods=["POST"])
def upload_image():
    """Upload an image - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Gallery endpoints coming soon.", status_code=501)


@gallery_bp.route("/<string:image_id>", methods=["DELETE"])
def delete_image(image_id):
    """Delete an image - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Gallery endpoints coming soon.", status_code=501)
