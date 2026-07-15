"""Package routes: CRUD for packages, pricing tiers, and itineraries.

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
- 5.1: POST /packages creates a package (admin)
- 5.2: GET /packages returns paginated, filtered list (public)
- 5.3: PUT /packages/{id} updates a package (admin)
- 5.4: DELETE /packages/{id} soft-deletes a package (admin)
- 5.5: POST /packages/{id}/pricing-tiers adds a pricing tier (admin)
- 5.6: GET /packages/{id} returns full detail with itinerary (public)
       POST /packages/{id}/itineraries adds an itinerary day (admin)
"""

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.packages.schemas import (
    ItinerarySchema,
    PackageCreateSchema,
    PackageDetailSchema,
    PackageListSchema,
    PackageUpdateSchema,
    PricingTierSchema,
    PricingTierResponseSchema,
    ItineraryResponseSchema,
)
from app.middleware.auth_middleware import auth_required
from app.middleware.rbac_middleware import ADMIN_ROLES
from app.services.package_service import PackageService
from app.utils.exceptions import AppError
from app.utils.response import error_response, paginated_response, success_response

packages_bp = Blueprint("packages", __name__, url_prefix="/packages")


@packages_bp.route("", methods=["GET"])
def list_packages():
    """List packages with pagination, filtering, and search.

    Public endpoint - no authentication required.

    Query parameters:
        page (int): Page number (default 1)
        per_page (int): Items per page (default 20, max 100)
        destination_id (str): Filter by destination UUID
        traveller_type (str): Filter by traveller type
        min_duration (int): Minimum duration in days
        max_duration (int): Maximum duration in days
        min_price (float): Minimum price
        max_price (float): Maximum price
        search (str): Text search on title and description
        sort_by (str): Sort field (prefix with - for descending)

    Returns:
        Paginated list of packages.
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    destination_id = request.args.get("destination_id")
    traveller_type = request.args.get("traveller_type")
    min_duration = request.args.get("min_duration", type=int)
    max_duration = request.args.get("max_duration", type=int)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    search = request.args.get("search")
    sort_by = request.args.get("sort_by")

    service = PackageService()
    items, pagination_meta = service.list_packages(
        page=page,
        per_page=per_page,
        destination_id=destination_id,
        traveller_type=traveller_type,
        min_duration=min_duration,
        max_duration=max_duration,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
    )

    schema = PackageListSchema()
    return paginated_response(
        items=items,
        total=pagination_meta["total"],
        page=pagination_meta["page"],
        per_page=pagination_meta["per_page"],
        schema=schema,
    )


@packages_bp.route("/<string:package_id>", methods=["GET"])
def get_package(package_id):
    """Get full package details including pricing tiers and itinerary.

    Public endpoint - no authentication required.

    Args:
        package_id: UUID of the package.

    Returns:
        Full package data with pricing tiers and day-wise itinerary.
    """
    service = PackageService()

    try:
        package = service.get_detail(package_id)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    schema = PackageDetailSchema()
    return success_response(
        schema.dump(package),
        message="Package retrieved successfully.",
    )


@packages_bp.route("", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def create_package():
    """Create a new travel package.

    Admin-only endpoint.
    Request body: Package data including title, description, destination_id,
                  duration, traveller_type, inclusions, exclusions, and optionally
                  pricing_tiers and itineraries.

    Returns:
        201 with created package data.
    Errors:
        409 (slug conflict), 422 (validation)
    """
    schema = PackageCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = PackageService()

    try:
        package = service.create_package(data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = PackageDetailSchema()
    return success_response(
        response_schema.dump(package),
        message="Package created successfully.",
        status_code=201,
    )


@packages_bp.route("/<string:package_id>", methods=["PUT"])
@auth_required(roles=ADMIN_ROLES)
def update_package(package_id):
    """Update an existing package.

    Admin-only endpoint.
    Request body: Fields to update (all optional).

    Args:
        package_id: UUID of the package to update.

    Returns:
        200 with updated package data.
    Errors:
        404 (not found), 422 (validation)
    """
    schema = PackageUpdateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "No fields to update.",
            status_code=422,
        )

    service = PackageService()

    try:
        package = service.update_package(package_id, data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = PackageDetailSchema()
    return success_response(
        response_schema.dump(package),
        message="Package updated successfully.",
    )


@packages_bp.route("/<string:package_id>", methods=["DELETE"])
@auth_required(roles=ADMIN_ROLES)
def delete_package(package_id):
    """Soft-delete a package.

    Admin-only endpoint.

    Args:
        package_id: UUID of the package to delete.

    Returns:
        200 with confirmation message.
    Errors:
        404 (not found)
    """
    service = PackageService()

    try:
        service.soft_delete_package(package_id)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    return success_response(
        None,
        message="Package deleted successfully.",
    )


@packages_bp.route("/<string:package_id>/pricing-tiers", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def add_pricing_tier(package_id):
    """Add a pricing tier to an existing package.

    Admin-only endpoint.
    Request body: {tier_name, price, max_persons?, description?}

    Args:
        package_id: UUID of the package.

    Returns:
        201 with created pricing tier data.
    Errors:
        404 (package not found), 409 (duplicate tier name), 422 (validation)
    """
    schema = PricingTierSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = PackageService()

    try:
        tier = service.add_pricing_tier(package_id, data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = PricingTierResponseSchema()
    return success_response(
        response_schema.dump(tier),
        message="Pricing tier added successfully.",
        status_code=201,
    )


@packages_bp.route("/<string:package_id>/itineraries", methods=["POST"])
@auth_required(roles=ADMIN_ROLES)
def add_itinerary(package_id):
    """Add an itinerary day to an existing package.

    Admin-only endpoint.
    Request body: {day_number, title, description, activities?}

    Args:
        package_id: UUID of the package.

    Returns:
        201 with created itinerary data.
    Errors:
        404 (package not found), 409 (duplicate day number), 422 (validation)
    """
    schema = ItinerarySchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = PackageService()

    try:
        itinerary = service.add_itinerary_day(package_id, data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = ItineraryResponseSchema()
    return success_response(
        response_schema.dump(itinerary),
        message="Itinerary day added successfully.",
        status_code=201,
    )
