"""Blog routes - MVP Stub.

This module will implement blog post CRUD, publishing, and listing endpoints.
TODO: Implement in next iteration.

Requirements: 15.1, 15.2, 15.3, 15.4
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

blog_bp = Blueprint("blog", __name__, url_prefix="/blog")


@blog_bp.route("", methods=["GET"])
def list_posts():
    """List blog posts - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Blog endpoints coming soon.", status_code=501)


@blog_bp.route("/<string:slug>", methods=["GET"])
def get_post(slug):
    """Get blog post by slug - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Blog endpoints coming soon.", status_code=501)


@blog_bp.route("", methods=["POST"])
def create_post():
    """Create a blog post - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Blog endpoints coming soon.", status_code=501)
