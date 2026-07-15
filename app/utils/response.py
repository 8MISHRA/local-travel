"""Response helper utilities.

Provides consistent response formatting for all API endpoints.

Validates: Requirements 21.1, 21.2, 22.2
"""

from flask import jsonify


def success_response(data, message="Success", status_code=200):
    """Create a standardized success response.

    Args:
        data: The response payload (serializable object).
        message: Human-readable success message.
        status_code: HTTP status code (default 200).

    Returns:
        Tuple of (response_dict, status_code).
    """
    return jsonify({
        "success": True,
        "data": data,
        "message": message,
    }), status_code


def error_response(code, message, details=None, status_code=400):
    """Create a standardized error response.

    Args:
        code: Machine-readable error code string.
        message: Human-readable error description.
        details: Optional dict with additional error context.
        status_code: HTTP status code (default 400).

    Returns:
        Tuple of (response_dict, status_code).
    """
    return jsonify({
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }), status_code


def paginated_response(items, total, page, per_page, schema=None):
    """Create a standardized paginated list response.

    Args:
        items: List of items for the current page.
        total: Total number of items across all pages.
        page: Current page number.
        per_page: Number of items per page.
        schema: Optional Marshmallow schema instance to serialize items.
            If None, items are returned as-is.

    Returns:
        Tuple of (response_dict, status_code).
    """
    serialized = schema.dump(items, many=True) if schema else items
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return jsonify({
        "success": True,
        "data": serialized,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
        "message": "Success",
    }), 200
