"""Destination routes: CRUD for destinations and sub-destinations.

Validates: Requirements 6.1, 6.2, 6.3, 6.4
- 6.1: GET /destinations returns primary destinations with sub-destinations
- 6.2: POST /destinations/{id}/sub-destinations creates sub-destination
- 6.3: GET /destinations returns hierarchical structure
- 6.4: DELETE /destinations/{id} soft-deletes destination + sub-destinations
"""

from flask import Blueprint, request
from marshmallow import ValidationError as MarshmallowValidationError

from app.api.v1.destinations.schemas import (
    CreateDestinationSchema,
    CreateSubDestinationSchema,
    DestinationHierarchicalSchema,
    DestinationResponseSchema,
    SubDestinationResponseSchema,
    UpdateDestinationSchema,
)
from app.middleware.auth_middleware import auth_required
from app.services.destination_service import DestinationService
from app.utils.exceptions import AppError
from app.utils.response import error_response, success_response

destinations_bp = Blueprint("destinations", __name__, url_prefix="/destinations")


@destinations_bp.route("", methods=["GET"])
def list_destinations():
    """List all destinations with their sub-destinations in hierarchical structure.

    Public endpoint - no authentication required.
    Returns destinations with nested sub-destinations.
    """
    service = DestinationService()
    results = service.list_hierarchical()

    schema = DestinationHierarchicalSchema()
    data = []
    for item in results:
        dest = item["destination"]
        # Build the hierarchical object for serialization
        dest_data = schema.dump(dest)
        sub_schema = SubDestinationResponseSchema(many=True)
        dest_data["sub_destinations"] = sub_schema.dump(item["sub_destinations"])
        data.append(dest_data)

    return success_response(data, message="Destinations retrieved successfully.")


@destinations_bp.route("/<string:destination_id>", methods=["GET"])
def get_destination(destination_id):
    """Get a single destination with its sub-destinations.

    Public endpoint - no authentication required.

    Args:
        destination_id: UUID of the destination.
    """
    service = DestinationService()

    try:
        result = service.get_destination(destination_id)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    dest = result["destination"]
    schema = DestinationResponseSchema()
    dest_data = schema.dump(dest)

    sub_schema = SubDestinationResponseSchema(many=True)
    dest_data["sub_destinations"] = sub_schema.dump(result["sub_destinations"])

    return success_response(dest_data, message="Destination retrieved successfully.")


@destinations_bp.route("", methods=["POST"])
@auth_required(roles=["admin", "super_admin"])
def create_destination():
    """Create a new destination.

    Admin-only endpoint.
    Request body: {name, description?, is_primary?}
    Success: 201 with created destination data.
    Errors: 409 (duplicate name), 422 (validation)
    """
    schema = CreateDestinationSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = DestinationService()

    try:
        destination = service.create_destination(
            name=data["name"],
            description=data.get("description"),
            is_primary=data.get("is_primary", False),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = DestinationResponseSchema()
    return success_response(
        response_schema.dump(destination),
        message="Destination created successfully.",
        status_code=201,
    )


@destinations_bp.route("/<string:destination_id>/sub-destinations", methods=["POST"])
@auth_required(roles=["admin", "super_admin"])
def create_sub_destination(destination_id):
    """Create a sub-destination under a parent destination.

    Admin-only endpoint.
    Request body: {name, category, description?, latitude?, longitude?, media_urls?}
    Success: 201 with created sub-destination data.
    Errors: 404 (parent not found), 422 (validation)
    """
    schema = CreateSubDestinationSchema()
    try:
        data = schema.load(request.get_json() or {})
    except MarshmallowValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed.",
            details=e.messages,
            status_code=422,
        )

    service = DestinationService()

    try:
        sub_destination = service.create_sub_destination(
            destination_id=destination_id,
            name=data["name"],
            category=data["category"],
            description=data.get("description"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            media_urls=data.get("media_urls"),
        )
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = SubDestinationResponseSchema()
    return success_response(
        response_schema.dump(sub_destination),
        message="Sub-destination created successfully.",
        status_code=201,
    )


@destinations_bp.route("/<string:destination_id>", methods=["PUT"])
@auth_required(roles=["admin", "super_admin"])
def update_destination(destination_id):
    """Update a destination.

    Admin-only endpoint.
    Request body: {name?, description?, is_primary?}
    Success: 200 with updated destination data.
    Errors: 404 (not found), 409 (name conflict), 422 (validation)
    """
    schema = UpdateDestinationSchema()
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

    service = DestinationService()

    try:
        destination = service.update_destination(destination_id, **data)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    response_schema = DestinationResponseSchema()
    return success_response(
        response_schema.dump(destination),
        message="Destination updated successfully.",
    )


@destinations_bp.route("/<string:destination_id>", methods=["DELETE"])
@auth_required(roles=["admin", "super_admin"])
def delete_destination(destination_id):
    """Soft-delete a destination and its sub-destinations.

    Admin-only endpoint.
    Success: 200 with confirmation message.
    Errors: 404 (not found)
    """
    service = DestinationService()

    try:
        service.soft_delete_destination(destination_id)
    except AppError as e:
        return error_response(e.code, e.message, e.details, status_code=e.status_code)

    return success_response(
        None,
        message="Destination deleted successfully.",
    )
