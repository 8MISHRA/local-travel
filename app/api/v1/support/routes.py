"""Support ticket routes - MVP Stub.

This module will implement support ticket creation, reply, status update, and listing.
TODO: Implement in next iteration.

Requirements: 20.1, 20.2, 20.3, 20.4
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

support_bp = Blueprint("support", __name__, url_prefix="/support-tickets")


@support_bp.route("", methods=["GET"])
def list_tickets():
    """List support tickets - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Support ticket endpoints coming soon.", status_code=501)


@support_bp.route("", methods=["POST"])
def create_ticket():
    """Create a support ticket - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Support ticket endpoints coming soon.", status_code=501)


@support_bp.route("/<string:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """Get support ticket details - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Support ticket endpoints coming soon.", status_code=501)


@support_bp.route("/<string:ticket_id>/replies", methods=["POST"])
def add_reply(ticket_id):
    """Add reply to a support ticket - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Support ticket endpoints coming soon.", status_code=501)


@support_bp.route("/<string:ticket_id>/status", methods=["PATCH"])
def update_ticket_status(ticket_id):
    """Update support ticket status - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Support ticket endpoints coming soon.", status_code=501)
