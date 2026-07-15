"""Property-based tests for package filtering and soft delete.

**Validates: Requirements 5.2, 5.4, 23.2**

Tests:
- Property 9: Package filtering returns only matching results
- Property 8: Soft-deleted entities are excluded from listings
"""

import uuid
from datetime import datetime, timezone

from hypothesis import given, settings, assume
from hypothesis import strategies as st

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.models.package import TravellerType
from app.repositories.package_repository import PackageRepository


# ---------------------------------------------------------------------------
# Helpers: In-memory SQLAlchemy setup for property tests
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class FakeDestination(Base):
    """Minimal destination model for FK reference in tests."""

    __tablename__ = "destinations"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = sa.Column(sa.String(100), nullable=False, unique=True)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    deleted_at = sa.Column(sa.DateTime, nullable=True)


class FakePackage(Base):
    """Package model mirroring the production schema for in-memory testing."""

    __tablename__ = "packages"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = sa.Column(sa.String(255), nullable=False)
    slug = sa.Column(sa.String(255), unique=True, nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    destination_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("destinations.id"),
        nullable=False,
    )
    duration_days = sa.Column(sa.Integer, nullable=False)
    duration_nights = sa.Column(sa.Integer, nullable=False)
    traveller_type = sa.Column(
        sa.Enum(TravellerType, name="traveller_type_enum"),
        nullable=False,
    )
    inclusions = sa.Column(sa.JSON, nullable=False)
    exclusions = sa.Column(sa.JSON, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)
    featured_image_url = sa.Column(sa.String(500), nullable=True)
    average_rating = sa.Column(sa.Numeric(3, 2), default=0.00)
    total_reviews = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    deleted_at = sa.Column(sa.DateTime, nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = datetime.now(timezone.utc)


class FakePricingTier(Base):
    """PricingTier model for price-based filtering tests."""

    __tablename__ = "pricing_tiers"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    tier_name = sa.Column(sa.String(50), nullable=False)
    price = sa.Column(sa.Numeric(10, 2), nullable=False)
    max_persons = sa.Column(sa.Integer, nullable=True)
    description = sa.Column(sa.String(255), nullable=True)


class FakeItinerary(Base):
    """Itinerary model stub for schema compatibility."""

    __tablename__ = "itineraries"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_number = sa.Column(sa.Integer, nullable=False)
    title = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    activities = sa.Column(sa.JSON, nullable=False)


def make_session():
    """Create an in-memory SQLite session with all required tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def create_destination(session, name):
    """Create a destination record and return its id."""
    now = datetime.now(timezone.utc)
    dest = FakeDestination(
        id=str(uuid.uuid4()),
        name=name,
        created_at=now,
        updated_at=now,
    )
    session.add(dest)
    session.flush()
    return dest.id


def create_package(session, destination_id, traveller_type, duration_days,
                   is_active=True, deleted_at=None, slug_suffix=None):
    """Create a package record and return it."""
    now = datetime.now(timezone.utc)
    pkg_id = str(uuid.uuid4())
    slug = f"pkg-{pkg_id[:8]}" if slug_suffix is None else slug_suffix
    pkg = FakePackage(
        id=pkg_id,
        title=f"Package {pkg_id[:8]}",
        slug=slug,
        description=f"Description for {pkg_id[:8]}",
        destination_id=destination_id,
        duration_days=duration_days,
        duration_nights=max(0, duration_days - 1),
        traveller_type=traveller_type,
        inclusions=["breakfast"],
        exclusions=["flights"],
        is_active=is_active,
        created_at=now,
        updated_at=now,
        deleted_at=deleted_at,
    )
    session.add(pkg)
    session.flush()
    return pkg


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

st_traveller_type = st.sampled_from(list(TravellerType))
st_duration = st.integers(min_value=1, max_value=30)
st_num_packages = st.integers(min_value=1, max_value=20)
st_destination_index = st.integers(min_value=0, max_value=2)


# ---------------------------------------------------------------------------
# Property 9: Package filtering returns only matching results
# ---------------------------------------------------------------------------

class TestPackageFilteringReturnsMatching:
    """Property 9: Package filtering returns only matching results.

    **Validates: Requirements 5.2**

    When filtered by destination, traveller_type, or duration, only packages
    matching ALL applied filters are returned. No items violating the filter
    criteria should be included in results.
    """

    @settings(max_examples=100)
    @given(
        package_configs=st.lists(
            st.tuples(
                st_destination_index,
                st_traveller_type,
                st_duration,
            ),
            min_size=2,
            max_size=15,
        ),
        filter_dest_idx=st.integers(min_value=0, max_value=2),
    )
    def test_filter_by_destination_returns_only_matching(
        self, package_configs, filter_dest_idx
    ):
        """**Validates: Requirements 5.2**

        When filtering by destination_id, all returned packages must have
        that exact destination_id. No package with a different destination
        should appear.
        """
        session = make_session()

        # Create 3 destinations
        dest_ids = [
            create_destination(session, f"Dest_{i}_{uuid.uuid4().hex[:6]}")
            for i in range(3)
        ]

        # Create packages with various configurations
        for dest_idx, tt, dur in package_configs:
            create_package(session, dest_ids[dest_idx], tt, dur)

        session.commit()

        # Use the real PackageRepository with the test session
        # We need to monkey-patch the model_class since the repository
        # references the production model
        repo = PackageRepository(session)
        # Override model_class to use our FakePackage
        repo.model_class = FakePackage

        target_dest_id = dest_ids[filter_dest_idx]
        items, _meta = repo.list_packages(
            page=1, per_page=100, destination_id=target_dest_id
        )

        # Property: ALL returned items must match the filter
        for item in items:
            assert item.destination_id == target_dest_id

        session.close()

    @settings(max_examples=100)
    @given(
        package_configs=st.lists(
            st.tuples(
                st_destination_index,
                st_traveller_type,
                st_duration,
            ),
            min_size=2,
            max_size=15,
        ),
        filter_type=st_traveller_type,
    )
    def test_filter_by_traveller_type_returns_only_matching(
        self, package_configs, filter_type
    ):
        """**Validates: Requirements 5.2**

        When filtering by traveller_type, all returned packages must have
        that exact traveller_type.
        """
        session = make_session()

        dest_ids = [
            create_destination(session, f"Dest_{i}_{uuid.uuid4().hex[:6]}")
            for i in range(3)
        ]

        for dest_idx, tt, dur in package_configs:
            create_package(session, dest_ids[dest_idx], tt, dur)

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        items, _meta = repo.list_packages(
            page=1, per_page=100, traveller_type=filter_type
        )

        for item in items:
            assert item.traveller_type == filter_type

        session.close()

    @settings(max_examples=100)
    @given(
        package_configs=st.lists(
            st.tuples(
                st_destination_index,
                st_traveller_type,
                st_duration,
            ),
            min_size=2,
            max_size=15,
        ),
        min_dur=st.integers(min_value=1, max_value=15),
        max_dur=st.integers(min_value=15, max_value=30),
    )
    def test_filter_by_duration_range_returns_only_matching(
        self, package_configs, min_dur, max_dur
    ):
        """**Validates: Requirements 5.2**

        When filtering by duration range (min_duration, max_duration), all
        returned packages must have duration_days within [min_dur, max_dur].
        """
        assume(min_dur <= max_dur)

        session = make_session()

        dest_ids = [
            create_destination(session, f"Dest_{i}_{uuid.uuid4().hex[:6]}")
            for i in range(3)
        ]

        for dest_idx, tt, dur in package_configs:
            create_package(session, dest_ids[dest_idx], tt, dur)

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        items, _meta = repo.list_packages(
            page=1, per_page=100, min_duration=min_dur, max_duration=max_dur
        )

        for item in items:
            assert min_dur <= item.duration_days <= max_dur

        session.close()

    @settings(max_examples=100)
    @given(
        package_configs=st.lists(
            st.tuples(
                st_destination_index,
                st_traveller_type,
                st_duration,
            ),
            min_size=3,
            max_size=15,
        ),
        filter_dest_idx=st.integers(min_value=0, max_value=2),
        filter_type=st_traveller_type,
    )
    def test_combined_filters_all_must_match(
        self, package_configs, filter_dest_idx, filter_type
    ):
        """**Validates: Requirements 5.2**

        When multiple filters are applied simultaneously (destination + traveller_type),
        ALL returned packages must satisfy EVERY filter condition.
        """
        session = make_session()

        dest_ids = [
            create_destination(session, f"Dest_{i}_{uuid.uuid4().hex[:6]}")
            for i in range(3)
        ]

        for dest_idx, tt, dur in package_configs:
            create_package(session, dest_ids[dest_idx], tt, dur)

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        target_dest_id = dest_ids[filter_dest_idx]
        items, _meta = repo.list_packages(
            page=1,
            per_page=100,
            destination_id=target_dest_id,
            traveller_type=filter_type,
        )

        for item in items:
            assert item.destination_id == target_dest_id
            assert item.traveller_type == filter_type

        session.close()

    @settings(max_examples=100)
    @given(
        package_configs=st.lists(
            st.tuples(
                st_destination_index,
                st_traveller_type,
                st_duration,
            ),
            min_size=3,
            max_size=15,
        ),
        filter_dest_idx=st.integers(min_value=0, max_value=2),
        filter_type=st_traveller_type,
        min_dur=st.integers(min_value=1, max_value=10),
        max_dur=st.integers(min_value=20, max_value=30),
    )
    def test_triple_filter_destination_type_duration(
        self, package_configs, filter_dest_idx, filter_type, min_dur, max_dur
    ):
        """**Validates: Requirements 5.2**

        When all three filters (destination, traveller_type, duration) are
        applied, every returned package must match ALL three criteria.
        """
        session = make_session()

        dest_ids = [
            create_destination(session, f"Dest_{i}_{uuid.uuid4().hex[:6]}")
            for i in range(3)
        ]

        for dest_idx, tt, dur in package_configs:
            create_package(session, dest_ids[dest_idx], tt, dur)

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        target_dest_id = dest_ids[filter_dest_idx]
        items, _meta = repo.list_packages(
            page=1,
            per_page=100,
            destination_id=target_dest_id,
            traveller_type=filter_type,
            min_duration=min_dur,
            max_duration=max_dur,
        )

        for item in items:
            assert item.destination_id == target_dest_id
            assert item.traveller_type == filter_type
            assert min_dur <= item.duration_days <= max_dur

        session.close()


# ---------------------------------------------------------------------------
# Property 8: Soft-deleted entities are excluded from listings
# ---------------------------------------------------------------------------

class TestSoftDeleteExclusion:
    """Property 8: Soft-deleted entities are excluded from listings.

    **Validates: Requirements 5.4, 23.2**

    Soft-deleted packages (those with deleted_at set) must never appear
    in list_packages results, regardless of filter combination.
    """

    @settings(max_examples=100)
    @given(
        num_active=st.integers(min_value=0, max_value=10),
        num_deleted=st.integers(min_value=1, max_value=10),
    )
    def test_soft_deleted_packages_never_in_listing(self, num_active, num_deleted):
        """**Validates: Requirements 5.4, 23.2**

        For any mix of active and soft-deleted packages, the listing endpoint
        must never return a package that has deleted_at set.
        """
        session = make_session()

        dest_id = create_destination(session, f"Dest_{uuid.uuid4().hex[:8]}")
        now = datetime.now(timezone.utc)

        # Create active packages
        active_ids = set()
        for i in range(num_active):
            pkg = create_package(
                session, dest_id, TravellerType.solo, 3,
                is_active=True, deleted_at=None,
            )
            active_ids.add(pkg.id)

        # Create soft-deleted packages
        deleted_ids = set()
        for i in range(num_deleted):
            pkg = create_package(
                session, dest_id, TravellerType.solo, 3,
                is_active=True, deleted_at=now,
            )
            deleted_ids.add(pkg.id)

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        items, meta = repo.list_packages(page=1, per_page=100)

        returned_ids = {item.id for item in items}

        # Property: NO soft-deleted package should appear in results
        assert returned_ids.isdisjoint(deleted_ids)

        # Sanity: all returned items should be from active set
        assert returned_ids.issubset(active_ids)

        # Metadata total should only count active packages
        assert meta["total"] == num_active

        session.close()

    @settings(max_examples=100)
    @given(
        num_active=st.integers(min_value=1, max_value=10),
        num_deleted=st.integers(min_value=1, max_value=10),
        filter_type=st_traveller_type,
    )
    def test_soft_deleted_excluded_even_with_matching_filters(
        self, num_active, num_deleted, filter_type
    ):
        """**Validates: Requirements 5.4, 23.2**

        Even if a soft-deleted package matches the applied filter criteria,
        it must still be excluded from results.
        """
        session = make_session()

        dest_id = create_destination(session, f"Dest_{uuid.uuid4().hex[:8]}")
        now = datetime.now(timezone.utc)

        # Create active packages matching the filter type
        for i in range(num_active):
            create_package(
                session, dest_id, filter_type, 5,
                is_active=True, deleted_at=None,
            )

        # Create soft-deleted packages that ALSO match the filter type
        deleted_ids = set()
        for i in range(num_deleted):
            pkg = create_package(
                session, dest_id, filter_type, 5,
                is_active=True, deleted_at=now,
            )
            deleted_ids.add(pkg.id)

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        items, _meta = repo.list_packages(
            page=1, per_page=100, traveller_type=filter_type
        )

        returned_ids = {item.id for item in items}

        # Property: soft-deleted packages must not appear even though
        # they match the filter criteria
        assert returned_ids.isdisjoint(deleted_ids)

        session.close()

    @settings(max_examples=100)
    @given(
        num_packages=st.integers(min_value=2, max_value=15),
        delete_indices=st.lists(
            st.integers(min_value=0, max_value=14),
            min_size=1,
            max_size=8,
            unique=True,
        ),
    )
    def test_soft_delete_any_subset_excludes_those_from_listing(
        self, num_packages, delete_indices
    ):
        """**Validates: Requirements 5.4, 23.2**

        For any subset of packages that are soft-deleted, those packages
        and ONLY those packages are excluded from listing results.
        """
        # Ensure delete indices are within range
        valid_delete_indices = {i for i in delete_indices if i < num_packages}
        assume(len(valid_delete_indices) > 0)

        session = make_session()

        dest_id = create_destination(session, f"Dest_{uuid.uuid4().hex[:8]}")
        now = datetime.now(timezone.utc)

        all_packages = []
        for i in range(num_packages):
            deleted_at = now if i in valid_delete_indices else None
            pkg = create_package(
                session, dest_id, TravellerType.family, 7,
                is_active=True, deleted_at=deleted_at,
            )
            all_packages.append(pkg)

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        items, meta = repo.list_packages(page=1, per_page=100)

        returned_ids = {item.id for item in items}
        expected_active_ids = {
            all_packages[i].id
            for i in range(num_packages)
            if i not in valid_delete_indices
        }

        # Property: returned set equals exactly the non-deleted set
        assert returned_ids == expected_active_ids

        # Total count matches non-deleted count
        assert meta["total"] == len(expected_active_ids)

        session.close()

    @settings(max_examples=100)
    @given(
        num_packages=st.integers(min_value=1, max_value=10),
    )
    def test_all_deleted_returns_empty_listing(self, num_packages):
        """**Validates: Requirements 5.4, 23.2**

        If ALL packages are soft-deleted, the listing must return
        an empty result set with total=0.
        """
        session = make_session()

        dest_id = create_destination(session, f"Dest_{uuid.uuid4().hex[:8]}")
        now = datetime.now(timezone.utc)

        for i in range(num_packages):
            create_package(
                session, dest_id, TravellerType.couple, 4,
                is_active=True, deleted_at=now,
            )

        session.commit()

        repo = PackageRepository(session)
        repo.model_class = FakePackage

        items, meta = repo.list_packages(page=1, per_page=100)

        # Property: no results when everything is deleted
        assert len(items) == 0
        assert meta["total"] == 0

        session.close()
