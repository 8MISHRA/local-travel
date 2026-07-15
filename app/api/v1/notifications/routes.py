"""Notification routes - MVP Stub.

This module will implement notification listing, mark-read, and mark-all-read endpoints.
TODO: Implement in next iteration.

Requirements: 19.1, 19.2, 19.3, 19.4
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("", methods=["GET"])
def list_notifications():
    """List notifications - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Notification endpoints coming soon.", status_code=501)


@notifications_bp.route("/<string:notification_id>/read", methods=["PATCH"])
def mark_read(notification_id):
    """Mark notification as read - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Notification endpoints coming soon.", status_code=501)


@notifications_bp.route("/mark-all-read", methods=["POST"])
def mark_all_read():
    """Mark all notifications as read - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Notification endpoints coming soon.", status_code=501)
