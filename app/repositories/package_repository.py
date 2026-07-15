"""Package repository for data access operations on packages, pricing tiers, and itineraries.

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
- 5.1: Create packages with title, description, destination, duration, pricing, itinerary
- 5.2: Paginated listing with filtering by destination, duration, price range, traveller type
- 5.3: Update specified fields
- 5.4: Soft delete packages
- 5.5: Multiple pricing tiers per package
- 5.6: Day-wise itinerary breakdown
"""

import math

from sqlalchemy import or_

from app.models.package import Itinerary, Package, PricingTier
from app.repositories.base_repository import BaseRepository


class PackageRepository(BaseRepository):
    """Repository for Package model with extended filtering and search capabilities."""

    model_class = Package

    def list_packages(
        self,
        page=1,
        per_page=20,
        destination_id=None,
        traveller_type=None,
        min_duration=None,
        max_duration=None,
        min_price=None,
        max_price=None,
        search=None,
        sort_by=None,
    ):
        """Return paginated packages with advanced filtering.

        Supports filtering by destination, traveller type, duration range,
        price range (via PricingTier join), and text search on title/description.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (max 100).
            destination_id: Filter by destination UUID.
            traveller_type: Filter by TravellerType enum value.
            min_duration: Minimum duration_days (inclusive).
            max_duration: Maximum duration_days (inclusive).
            min_price: Minimum price across any pricing tier.
            max_price: Maximum price across any pricing tier.
            search: Text search term applied to title and description.
            sort_by: Sort field ("field" asc, "-field" desc).

        Returns:
            Tuple of (items, pagination_metadata).
        """
        page = max(1, page)
        per_page = max(1, min(per_page, 100))

        query = self.session.query(Package).filter(
            Package.deleted_at.is_(None),
            Package.is_active.is_(True),
        )

        # Filter by destination
        if destination_id:
            query = query.filter(Package.destination_id == destination_id)

        # Filter by traveller type
        if traveller_type:
            query = query.filter(Package.traveller_type == traveller_type)

        # Filter by duration range
        if min_duration is not None:
            query = query.filter(Package.duration_days >= min_duration)
        if max_duration is not None:
            query = query.filter(Package.duration_days <= max_duration)

        # Filter by price range via PricingTier join
        if min_price is not None or max_price is not None:
            query = query.join(PricingTier, Package.id == PricingTier.package_id)
            if min_price is not None:
                query = query.filter(PricingTier.price >= min_price)
            if max_price is not None:
                query = query.filter(PricingTier.price <= max_price)
            query = query.distinct()

        # Text search on title and description
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Package.title.ilike(search_term),
                    Package.description.ilike(search_term),
                )
            )

        # Apply sorting
        if sort_by:
            query = self._apply_sorting(query, sort_by)
        else:
            query = query.order_by(Package.created_at.desc())

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

    def get_detail(self, package_id):
        """Get a package with its pricing tiers and itineraries eagerly loaded.

        Args:
            package_id: UUID of the package.

        Returns:
            Package instance with pricing_tiers and itineraries accessible,
            or None if not found/deleted.
        """
        package = self.session.query(Package).filter(
            Package.id == package_id,
            Package.deleted_at.is_(None),
        ).first()

        if package is None:
            return None

        # Force-load relationships (they use lazy="dynamic", so we convert to list)
        # Access them so they are available on the returned object
        _ = package.pricing_tiers.all()
        _ = package.itineraries.order_by(Itinerary.day_number.asc()).all()

        return package

    def create_pricing_tier(self, **kwargs):
        """Create a new pricing tier for a package.

        Args:
            **kwargs: PricingTier fields (package_id, tier_name, price, etc.)

        Returns:
            The created PricingTier instance.
        """
        tier = PricingTier(**kwargs)
        self.session.add(tier)
        self.session.flush()
        return tier

    def create_itinerary(self, **kwargs):
        """Create a new itinerary day for a package.

        Args:
            **kwargs: Itinerary fields (package_id, day_number, title, etc.)

        Returns:
            The created Itinerary instance.
        """
        itinerary = Itinerary(**kwargs)
        self.session.add(itinerary)
        self.session.flush()
        return itinerary

    def get_pricing_tier_by_package_and_name(self, package_id, tier_name):
        """Check if a pricing tier with the given name exists for a package.

        Args:
            package_id: UUID of the package.
            tier_name: Name of the tier.

        Returns:
            PricingTier instance or None.
        """
        return self.session.query(PricingTier).filter(
            PricingTier.package_id == package_id,
            PricingTier.tier_name == tier_name,
        ).first()

    def get_itinerary_by_package_and_day(self, package_id, day_number):
        """Check if an itinerary day with the given number exists for a package.

        Args:
            package_id: UUID of the package.
            day_number: Day number to check.

        Returns:
            Itinerary instance or None.
        """
        return self.session.query(Itinerary).filter(
            Itinerary.package_id == package_id,
            Itinerary.day_number == day_number,
        ).first()

    def find_by_slug(self, slug):
        """Find a non-deleted package by its slug.

        Args:
            slug: URL-friendly slug string.

        Returns:
            Package instance or None.
        """
        return self.session.query(Package).filter(
            Package.slug == slug,
            Package.deleted_at.is_(None),
        ).first()
