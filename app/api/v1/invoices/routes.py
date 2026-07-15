"""Invoice routes - MVP Stub.

This module will implement invoice generation and retrieval endpoints.
TODO: Implement in next iteration.

Requirements: 12.1, 12.2, 12.3
See design.md for full specification.
"""

from flask import Blueprint

from app.utils.response import error_response

invoices_bp = Blueprint("invoices", __name__, url_prefix="/invoices")


@invoices_bp.route("", methods=["GET"])
def list_invoices():
    """List invoices - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Invoice endpoints coming soon.", status_code=501)


@invoices_bp.route("/<string:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    """Get invoice by ID - TODO: implement."""
    return error_response("NOT_IMPLEMENTED", "Invoice endpoints coming soon.", status_code=501)
