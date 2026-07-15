"""Destination service with business logic for destination and sub-destination management.

Validates: Requirements 6.1, 6.2, 6.3, 6.4
- 6.1: Support primary destinations with configurable sub-destinations
- 6.2: Sub-destinations associated with parent, storing name, description,
       coordinates, category, and media references
- 6.3: Hierarchical listing of destinations with nested sub-destinations
- 6.4: Soft delete cascades to associated sub-destinations
"""

from app.extensions import db
from app.models.destination import SubDestinationCategory
from app.repositories.destination_repository import (
    DestinationRepository,
    SubDestinationRepository,
)
from app.utils.exceptions import ConflictError, NotFoundError, ValidationError


class DestinationService:
    """Service layer for destination and sub-destination operations."""

    def __init__(self):
        self.destination_repo = DestinationRepository(db.session)
        self.sub_destination_repo = SubDestinationRepository(db.session)

    def create_destination(self, name, description=None, is_primary=False):
        """Create a new destination.

        Args:
            name: Unique destination name.
            description: Optional description text.
            is_primary: Whether this is a primary destination.

        Returns:
            The created Destination instance.

        Raises:
            ConflictError: If a destination with the same name already exists.
        """
        # Check for duplicate name
        existing = db.session.query(
            self.destination_repo.model_class
        ).filter(
            self.destination_repo.model_class.name == name,
            self.destination_repo.model_class.deleted_at.is_(None),
        ).first()

        if existing:
            raise ConflictError(
                message=f"A destination with name '{name}' already exists.",
            )

        destination = self.destination_repo.create(
            name=name,
            description=description,
            is_primary=is_primary,
        )
        db.session.commit()
        return destination

    def create_sub_destination(
        self,
        destination_id,
        name,
        category,
        description=None,
        latitude=None,
        longitude=None,
        media_urls=None,
    ):
        """Create a sub-destination under a parent destination.

        Args:
            destination_id: UUID of the parent destination.
            name: Sub-destination name.
            category: Category string (must be valid SubDestinationCategory).
            description: Optional description.
            latitude: Optional latitude coordinate.
            longitude: Optional longitude coordinate.
            media_urls: Optional list of media URLs.

        Returns:
            The created SubDestination instance.

        Raises:
            NotFoundError: If parent destination doesn't exist.
            ValidationError: If category is invalid.
        """
        # Verify parent destination exists
        destination = self.destination_repo.get_by_id(destination_id)
        if destination is None:
            raise NotFoundError(
                message=f"Destination with id '{destination_id}' not found.",
            )

        # Validate category
        try:
            category_enum = SubDestinationCategory(category)
        except ValueError:
            valid_categories = [c.value for c in SubDestinationCategory]
            raise ValidationError(
                message=f"Invalid category '{category}'.",
                details={"category": [f"Must be one of: {', '.join(valid_categories)}"]},
            )

        sub_destination = self.sub_destination_repo.create(
            destination_id=destination_id,
            name=name,
            description=description,
            latitude=latitude,
            longitude=longitude,
            category=category_enum,
            media_urls=media_urls,
        )
        db.session.commit()
        return sub_destination

    def list_hierarchical(self):
        """List all destinations with their nested sub-destinations.

        Returns:
            List of Destination objects with associated sub-destinations.
        """
        destinations = self.destination_repo.list_hierarchical()

        result = []
        for dest in destinations:
            sub_destinations = self.sub_destination_repo.list_by_destination(dest.id)
            result.append({
                "destination": dest,
                "sub_destinations": sub_destinations,
            })

        return result

    def get_destination(self, destination_id):
        """Get a single destination with its sub-destinations.

        Args:
            destination_id: UUID of the destination.

        Returns:
            Dict with destination and sub_destinations.

        Raises:
            NotFoundError: If destination doesn't exist.
        """
        destination = self.destination_repo.get_by_id(destination_id)
        if destination is None:
            raise NotFoundError(
                message=f"Destination with id '{destination_id}' not found.",
            )

        sub_destinations = self.sub_destination_repo.list_by_destination(destination_id)

        return {
            "destination": destination,
            "sub_destinations": sub_destinations,
        }

    def update_destination(self, destination_id, **kwargs):
        """Update a destination's fields.

        Args:
            destination_id: UUID of the destination to update.
            **kwargs: Fields to update (name, description, is_primary).

        Returns:
            The updated Destination instance.

        Raises:
            NotFoundError: If destination doesn't exist.
            ConflictError: If new name conflicts with an existing destination.
        """
        destination = self.destination_repo.get_by_id(destination_id)
        if destination is None:
            raise NotFoundError(
                message=f"Destination with id '{destination_id}' not found.",
            )

        # Check for name uniqueness if name is being updated
        if "name" in kwargs and kwargs["name"] != destination.name:
            existing = db.session.query(
                self.destination_repo.model_class
            ).filter(
                self.destination_repo.model_class.name == kwargs["name"],
                self.destination_repo.model_class.deleted_at.is_(None),
                self.destination_repo.model_class.id != destination_id,
            ).first()

            if existing:
                raise ConflictError(
                    message=f"A destination with name '{kwargs['name']}' already exists.",
                )

        updated = self.destination_repo.update(destination_id, **kwargs)
        db.session.commit()
        return updated

    def soft_delete_destination(self, destination_id):
        """Soft-delete a destination and cascade to its sub-destinations.

        Args:
            destination_id: UUID of the destination to delete.

        Returns:
            The soft-deleted Destination instance.

        Raises:
            NotFoundError: If destination doesn't exist.
        """
        destination = self.destination_repo.soft_delete_cascade(destination_id)
        if destination is None:
            raise NotFoundError(
                message=f"Destination with id '{destination_id}' not found.",
            )

        db.session.commit()
        return destination
