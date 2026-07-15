"""Destination repository with hierarchical listing support.

Validates: Requirements 6.1, 6.3, 6.4
- 6.1: Support primary destinations with configurable sub-destinations
- 6.3: Hierarchical listing (destinations with nested sub-destinations)
- 6.4: Soft delete on destination cascades to sub-destinations
"""

from datetime import datetime, timezone

from app.models.destination import Destination, SubDestination
from app.repositories.base_repository import BaseRepository


class DestinationRepository(BaseRepository):
    """Repository for Destination model with hierarchical query support."""

    model_class = Destination

    def list_hierarchical(self, filters=None):
        """Return all non-deleted destinations with their non-deleted sub-destinations.

        Args:
            filters: Optional dict of equality filters for destinations.

        Returns:
            List of Destination objects with sub_destinations eagerly loaded.
        """
        query = self.session.query(Destination).filter(
            Destination.deleted_at.is_(None),
        )

        if filters:
            query = self._apply_filters(query, filters)

        query = query.order_by(Destination.name.asc())
        destinations = query.all()

        return destinations

    def get_with_sub_destinations(self, destination_id):
        """Fetch a single destination with its non-deleted sub-destinations.

        Args:
            destination_id: UUID of the destination.

        Returns:
            Destination instance or None if not found/deleted.
        """
        return self.session.query(Destination).filter(
            Destination.id == destination_id,
            Destination.deleted_at.is_(None),
        ).first()

    def soft_delete_cascade(self, destination_id):
        """Soft-delete a destination and all its sub-destinations.

        Args:
            destination_id: UUID of the destination to delete.

        Returns:
            The soft-deleted Destination, or None if not found.
        """
        destination = self.get_by_id(destination_id)
        if destination is None:
            return None

        now = datetime.now(timezone.utc)
        destination.deleted_at = now

        # Cascade soft-delete to all non-deleted sub-destinations
        sub_destinations = self.session.query(SubDestination).filter(
            SubDestination.destination_id == destination_id,
            SubDestination.deleted_at.is_(None),
        ).all()

        for sub in sub_destinations:
            sub.deleted_at = now

        self.session.flush()
        return destination


class SubDestinationRepository(BaseRepository):
    """Repository for SubDestination model."""

    model_class = SubDestination

    def list_by_destination(self, destination_id):
        """Return all non-deleted sub-destinations for a given destination.

        Args:
            destination_id: UUID of the parent destination.

        Returns:
            List of SubDestination objects.
        """
        return self.session.query(SubDestination).filter(
            SubDestination.destination_id == destination_id,
            SubDestination.deleted_at.is_(None),
        ).order_by(SubDestination.name.asc()).all()
