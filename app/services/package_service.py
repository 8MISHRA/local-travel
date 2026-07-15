"""Package service providing business logic for package management.

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
- 5.1: Create packages with title, description, destination, duration, pricing tiers, itinerary
- 5.2: Paginated listing with filtering by destination, duration, price range, traveller type
- 5.3: Update specified fields and record updated_at timestamp
- 5.4: Soft delete packages
- 5.5: Multiple pricing tiers per package (per_person, couple, family, group)
- 5.6: Full package detail including day-wise itinerary breakdown
"""

import re
import unicodedata
from datetime import datetime, timezone

from app.extensions import db
from app.repositories.package_repository import PackageRepository
from app.utils.exceptions import ConflictError, NotFoundError, ValidationError


def slugify(text):
    """Generate a URL-friendly slug from the given text.

    Converts to lowercase, replaces non-alphanumeric characters with hyphens,
    and strips leading/trailing hyphens.

    Args:
        text: The input string to slugify.

    Returns:
        A URL-friendly slug string.
    """
    # Normalize unicode characters
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Convert to lowercase
    text = text.lower()
    # Replace any non-alphanumeric character with a hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    return text


class PackageService:
    """Service layer for package management operations.

    Handles creation, listing, detail retrieval, updates, soft deletion,
    and adding pricing tiers and itinerary days to existing packages.
    """

    def __init__(self, session=None):
        """Initialize the service with a database session.

        Args:
            session: SQLAlchemy session. Defaults to db.session if None.
        """
        self.session = session or db.session
        self.repo = PackageRepository(self.session)

    def create_package(self, data):
        """Create a new package with pricing tiers and itineraries in one transaction.

        Auto-generates a slug from the title. If the slug already exists,
        appends a numeric suffix to ensure uniqueness.

        Args:
            data: Dict containing:
                - title (str): Package title
                - description (str): Package description
                - destination_id (str): UUID of the destination
                - duration_days (int): Number of days
                - duration_nights (int): Number of nights
                - traveller_type (str): One of solo, couple, family, group, corporate
                - inclusions (list): List of included items
                - exclusions (list): List of excluded items
                - featured_image_url (str, optional): URL for featured image
                - pricing_tiers (list): List of dicts with tier_name, price, max_persons, description
                - itineraries (list): List of dicts with day_number, title, description, activities

        Returns:
            The created Package instance.

        Raises:
            ConflictError: If a unique slug cannot be generated.
            ValidationError: If required fields are missing.
        """
        # Generate slug from title
        slug = slugify(data["title"])
        slug = self._ensure_unique_slug(slug)

        # Extract nested data
        pricing_tiers_data = data.pop("pricing_tiers", [])
        itineraries_data = data.pop("itineraries", [])

        # Create the package
        package = self.repo.create(
            title=data["title"],
            slug=slug,
            description=data["description"],
            destination_id=data["destination_id"],
            duration_days=data["duration_days"],
            duration_nights=data["duration_nights"],
            traveller_type=data["traveller_type"],
            inclusions=data.get("inclusions", []),
            exclusions=data.get("exclusions", []),
            featured_image_url=data.get("featured_image_url"),
            is_active=data.get("is_active", True),
        )

        # Create pricing tiers
        for tier_data in pricing_tiers_data:
            self.repo.create_pricing_tier(
                package_id=package.id,
                tier_name=tier_data["tier_name"],
                price=tier_data["price"],
                max_persons=tier_data.get("max_persons"),
                description=tier_data.get("description"),
            )

        # Create itineraries
        for itinerary_data in itineraries_data:
            self.repo.create_itinerary(
                package_id=package.id,
                day_number=itinerary_data["day_number"],
                title=itinerary_data["title"],
                description=itinerary_data["description"],
                activities=itinerary_data.get("activities", []),
            )

        self.session.commit()
        return package

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
        """List packages with filtering, search, pagination, and sorting.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page (max 100).
            destination_id: Filter by destination UUID.
            traveller_type: Filter by traveller type string.
            min_duration: Minimum duration_days.
            max_duration: Maximum duration_days.
            min_price: Minimum price (across any pricing tier).
            max_price: Maximum price (across any pricing tier).
            search: Text search on title and description.
            sort_by: Sort field string.

        Returns:
            Tuple of (items, pagination_metadata).
        """
        return self.repo.list_packages(
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

    def get_detail(self, package_id):
        """Get full package details including pricing tiers and itineraries.

        Args:
            package_id: UUID of the package.

        Returns:
            Package instance with related data.

        Raises:
            NotFoundError: If package does not exist or is deleted.
        """
        package = self.repo.get_detail(package_id)
        if package is None:
            raise NotFoundError(f"Package with id '{package_id}' not found.")
        return package

    def update_package(self, package_id, data):
        """Update specified fields on an existing package.

        Args:
            package_id: UUID of the package to update.
            data: Dict of fields to update. Supports title, description,
                  destination_id, duration_days, duration_nights, traveller_type,
                  inclusions, exclusions, is_active, featured_image_url.

        Returns:
            The updated Package instance.

        Raises:
            NotFoundError: If package does not exist or is deleted.
        """
        package = self.repo.get_by_id(package_id)
        if package is None:
            raise NotFoundError(f"Package with id '{package_id}' not found.")

        # If title is being updated, regenerate the slug
        if "title" in data and data["title"] != package.title:
            new_slug = slugify(data["title"])
            new_slug = self._ensure_unique_slug(new_slug, exclude_id=package_id)
            data["slug"] = new_slug

        # Update the fields
        updated_package = self.repo.update(package_id, **data)
        self.session.commit()
        return updated_package

    def soft_delete_package(self, package_id):
        """Soft delete a package by setting its deleted_at timestamp.

        Args:
            package_id: UUID of the package to delete.

        Returns:
            The soft-deleted Package instance.

        Raises:
            NotFoundError: If package does not exist or is already deleted.
        """
        package = self.repo.get_by_id(package_id)
        if package is None:
            raise NotFoundError(f"Package with id '{package_id}' not found.")

        self.repo.soft_delete(package_id)
        self.session.commit()
        return package

    def add_pricing_tier(self, package_id, tier_data):
        """Add a new pricing tier to an existing package.

        Args:
            package_id: UUID of the package.
            tier_data: Dict with tier_name, price, max_persons (optional),
                       description (optional).

        Returns:
            The created PricingTier instance.

        Raises:
            NotFoundError: If package does not exist or is deleted.
            ConflictError: If a tier with the same name already exists for this package.
        """
        package = self.repo.get_by_id(package_id)
        if package is None:
            raise NotFoundError(f"Package with id '{package_id}' not found.")

        # Check for duplicate tier name
        existing_tier = self.repo.get_pricing_tier_by_package_and_name(
            package_id, tier_data["tier_name"]
        )
        if existing_tier is not None:
            raise ConflictError(
                f"Pricing tier '{tier_data['tier_name']}' already exists for this package."
            )

        tier = self.repo.create_pricing_tier(
            package_id=package_id,
            tier_name=tier_data["tier_name"],
            price=tier_data["price"],
            max_persons=tier_data.get("max_persons"),
            description=tier_data.get("description"),
        )
        self.session.commit()
        return tier

    def add_itinerary_day(self, package_id, itinerary_data):
        """Add a new itinerary day to an existing package.

        Args:
            package_id: UUID of the package.
            itinerary_data: Dict with day_number, title, description, activities.

        Returns:
            The created Itinerary instance.

        Raises:
            NotFoundError: If package does not exist or is deleted.
            ConflictError: If an itinerary with the same day_number already exists.
        """
        package = self.repo.get_by_id(package_id)
        if package is None:
            raise NotFoundError(f"Package with id '{package_id}' not found.")

        # Check for duplicate day number
        existing_day = self.repo.get_itinerary_by_package_and_day(
            package_id, itinerary_data["day_number"]
        )
        if existing_day is not None:
            raise ConflictError(
                f"Itinerary day {itinerary_data['day_number']} already exists for this package."
            )

        itinerary = self.repo.create_itinerary(
            package_id=package_id,
            day_number=itinerary_data["day_number"],
            title=itinerary_data["title"],
            description=itinerary_data["description"],
            activities=itinerary_data.get("activities", []),
        )
        self.session.commit()
        return itinerary

    def _ensure_unique_slug(self, slug, exclude_id=None):
        """Ensure the slug is unique, appending a numeric suffix if needed.

        Args:
            slug: The base slug to check.
            exclude_id: Optional package ID to exclude from uniqueness check
                        (used during updates).

        Returns:
            A unique slug string.
        """
        candidate = slug
        counter = 1
        while True:
            existing = self.repo.find_by_slug(candidate)
            if existing is None:
                return candidate
            if exclude_id and existing.id == exclude_id:
                return candidate
            counter += 1
            candidate = f"{slug}-{counter}"
            if counter > 100:
                raise ConflictError(
                    f"Unable to generate unique slug for '{slug}'."
                )
