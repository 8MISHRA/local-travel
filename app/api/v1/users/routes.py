"""User management routes - MVP Stub.

This module will implement admin user management endpoints:
list users, get user, change role, soft delete.
TODO: Implement in next iteration.

Requirements: 4.1, 4.5
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("", methods=["GET"])
def list_users():
    """List users (admin) - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "User management endpoints coming soon.", status_code=501)


@users_bp.route("/<string:user_id>", methods=["GET"])
def get_user(user_id):
    """Get user by ID (admin) - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "User management endpoints coming soon.", status_code=501)


@users_bp.route("/<string:user_id>/role", methods=["PATCH"])
def update_user_role(user_id):
    """Update user role (super_admin) - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "User management endpoints coming soon.", status_code=501)


@users_bp.route("/<string:user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Soft delete user (super_admin) - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "User management endpoints coming soon.", status_code=501)
