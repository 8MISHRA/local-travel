"""Base repository providing common data access patterns.

Validates: Requirements 22.1, 22.2, 22.3, 23.2
- 22.1: Pagination with page/per_page (default 20, max 100)
- 22.2: Pagination metadata (total, page, per_page, total_pages)
- 22.3: Sorting via sort_by with "field_name" (asc) / "-field_name" (desc)
- 23.2: Soft-deleted records excluded from queries
"""

import math


class BaseRepository:
    """Generic repository with CRUD, pagination, filtering, and soft delete.

    Subclasses must set `model_class` to the SQLAlchemy model they manage.
    """

    model_class = None

    def __init__(self, session):
        self.session = session

    def get_by_id(self, entity_id):
        """Fetch a single non-deleted entity by its primary key.

        Returns None if the entity does not exist or has been soft-deleted.
        """
        return self.session.query(self.model_class).filter(
            self.model_class.id == entity_id,
            self.model_class.deleted_at.is_(None),
        ).first()

    def list_paginated(self, page=1, per_page=20, filters=None, sort_by=None):
        """Return a paginated, filtered, and sorted list of non-deleted entities.

        Args:
            page: Page number (1-indexed, default 1).
            per_page: Items per page (default 20, clamped to max 100).
            filters: Dict of {column_name: value} equality filters.
            sort_by: String field name for ascending or "-field_name" for descending.

        Returns:
            Tuple of (items, pagination_metadata) where pagination_metadata is a
            dict with keys: total, page, per_page, total_pages.
        """
        # Enforce pagination bounds
        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        query = self.session.query(self.model_class).filter(
            self.model_class.deleted_at.is_(None),
        )

        if filters:
            query = self._apply_filters(query, filters)
        if sort_by:
            query = self._apply_sorting(query, sort_by)

        total = query.count()
        total_pages = math.ceil(total / per_page) if total > 0 else 0
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        pagination_meta = {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

        return items, pagination_meta

    def create(self, **kwargs):
        """Create and persist a new entity.

        Returns the created instance (flushed but not committed).
        """
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, entity_id, **kwargs):
        """Update fields on an existing non-deleted entity.

        Returns the updated entity, or None if not found.
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            return None
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.session.flush()
        return entity

    def soft_delete(self, entity_id):
        """Soft-delete an entity by setting its deleted_at timestamp.

        Returns the entity if found (now marked deleted), or None.
        """
        entity = self.get_by_id(entity_id)
        if entity:
            entity.soft_delete()
            self.session.flush()
        return entity

    def _apply_filters(self, query, filters):
        """Apply equality filters from a dict of {column_name: value}.

        Skips keys that do not correspond to model columns.
        """
        for column_name, value in filters.items():
            column = getattr(self.model_class, column_name, None)
            if column is not None:
                query = query.filter(column == value)
        return query

    def _apply_sorting(self, query, sort_by):
        """Apply sorting based on sort_by string.

        Format:
            "field_name"  -> ascending order
            "-field_name" -> descending order

        If the field does not exist on the model, sorting is skipped.
        """
        if sort_by.startswith("-"):
            field_name = sort_by[1:]
            descending = True
        else:
            field_name = sort_by
            descending = False

        column = getattr(self.model_class, field_name, None)
        if column is not None:
            if descending:
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        return query
