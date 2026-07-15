"""Pagination utility for parsing and validating query parameters.

Validates: Requirements 22.1, 22.2, 22.3
"""

from flask import request


DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def get_pagination_params():
    """Extract and validate pagination parameters from the current request.

    Reads `page`, `per_page`, and `sort_by` from query string.

    Returns:
        dict with keys:
            - page (int): Current page number (min 1).
            - per_page (int): Items per page (min 1, max 100).
            - sort_by (str|None): Field name for sorting.
            - sort_dir (str): 'asc' or 'desc'.
    """
    try:
        page = int(request.args.get("page", DEFAULT_PAGE))
    except (TypeError, ValueError):
        page = DEFAULT_PAGE

    try:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except (TypeError, ValueError):
        per_page = DEFAULT_PER_PAGE

    # Clamp values to valid ranges
    page = max(1, page)
    per_page = max(1, min(per_page, MAX_PER_PAGE))

    # Parse sort_by: "field_name" for asc, "-field_name" for desc
    sort_by_raw = request.args.get("sort_by", None)
    sort_by = None
    sort_dir = "asc"

    if sort_by_raw:
        if sort_by_raw.startswith("-"):
            sort_by = sort_by_raw[1:]
            sort_dir = "desc"
        else:
            sort_by = sort_by_raw
            sort_dir = "asc"

    return {
        "page": page,
        "per_page": per_page,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }


def paginate_query(query, page, per_page):
    """Apply offset/limit pagination to a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object.
        page: Page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        Tuple of (items, total_count).
    """
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total
