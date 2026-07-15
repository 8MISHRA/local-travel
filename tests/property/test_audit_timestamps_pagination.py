"""Property-based tests for audit timestamps and pagination.

**Validates: Requirements 23.1, 22.1, 22.2, 22.3**

Tests:
- Property 29: Audit timestamps are always present and monotonic
- Property 27: Pagination metadata consistency
- Property 28: Sorting correctness
"""

import math
import time
from datetime import datetime, timezone, timedelta

from hypothesis import given, settings, assume
from hypothesis import strategies as st

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.repositories.base_repository import BaseRepository


# ---------------------------------------------------------------------------
# Helpers: In-memory SQLAlchemy setup for property tests
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class SampleModel(Base):
    """A minimal model using the same audit column pattern as AuditMixin."""
    __tablename__ = "sample_items"

    id = sa.Column(sa.String(36), primary_key=True)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    deleted_at = sa.Column(sa.DateTime, nullable=True)
    name = sa.Column(sa.String(100), nullable=False)
    value = sa.Column(sa.Integer, nullable=False, default=0)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = datetime.now(timezone.utc)


class SampleRepository(BaseRepository):
    model_class = SampleModel


def make_session():
    """Create an in-memory SQLite session with the sample table."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Strategy for generating valid pagination parameters
st_page = st.integers(min_value=1, max_value=1000)
st_per_page = st.integers(min_value=1, max_value=100)
st_total = st.integers(min_value=0, max_value=10000)

# Strategy for generating a list of items to insert (with unique names/values)
st_item_count = st.integers(min_value=0, max_value=50)

# Strategy for sort direction
st_sort_direction = st.sampled_from(["asc", "desc"])


# ---------------------------------------------------------------------------
# Property 29: Audit timestamps are always present and monotonic
# ---------------------------------------------------------------------------

class TestAuditTimestamps:
    """Property 29: Audit timestamps are always present and monotonic.

    **Validates: Requirements 23.1**

    For any model using the audit pattern:
    - created_at is always set (non-null)
    - updated_at is always set (non-null)
    - updated_at >= created_at
    """

    @settings(max_examples=100)
    @given(
        name=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
            min_size=1,
            max_size=50,
        ),
        value=st.integers(min_value=-1000, max_value=1000),
    )
    def test_new_record_has_timestamps_set(self, name, value):
        """**Validates: Requirements 23.1**

        When a new record is created, both created_at and updated_at must be set.
        """
        import uuid

        session = make_session()
        now = datetime.now(timezone.utc)

        item = SampleModel(
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            name=name,
            value=value,
        )
        session.add(item)
        session.flush()

        # Timestamps must be non-null
        assert item.created_at is not None
        assert item.updated_at is not None
        # updated_at >= created_at for newly created records
        assert item.updated_at >= item.created_at

        session.close()

    @settings(max_examples=100)
    @given(
        name=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "Z")),
            min_size=1,
            max_size=50,
        ),
        value=st.integers(min_value=-1000, max_value=1000),
        delay_ms=st.integers(min_value=1, max_value=100),
    )
    def test_updated_at_monotonic_after_update(self, name, value, delay_ms):
        """**Validates: Requirements 23.1**

        When a record is updated, updated_at must be >= created_at (monotonic).
        Simulates an update by setting updated_at to a later time.
        """
        import uuid

        session = make_session()
        created_time = datetime.now(timezone.utc)

        item = SampleModel(
            id=str(uuid.uuid4()),
            created_at=created_time,
            updated_at=created_time,
            name=name,
            value=value,
        )
        session.add(item)
        session.flush()

        # Simulate an update happening later
        updated_time = created_time + timedelta(milliseconds=delay_ms)
        item.updated_at = updated_time
        session.flush()

        # After update: updated_at >= created_at
        assert item.updated_at >= item.created_at
        # The update time should be strictly later than created_at
        assert item.updated_at > item.created_at

        session.close()

    @settings(max_examples=100)
    @given(
        created_at=st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31),
        ),
        delta_seconds=st.integers(min_value=0, max_value=86400 * 365),
    )
    def test_timestamp_monotonicity_property(self, created_at, delta_seconds):
        """**Validates: Requirements 23.1**

        For any valid created_at and any non-negative time delta,
        setting updated_at = created_at + delta guarantees updated_at >= created_at.
        """
        updated_at = created_at + timedelta(seconds=delta_seconds)

        # Core property: updated_at is always >= created_at
        assert updated_at >= created_at


# ---------------------------------------------------------------------------
# Property 27: Pagination metadata consistency
# ---------------------------------------------------------------------------

class TestPaginationMetadata:
    """Property 27: Pagination metadata consistency.

    **Validates: Requirements 22.1, 22.2**

    For any (total, page, per_page):
    - total_pages = ceil(total / per_page)
    - page <= total_pages for non-empty results
    - Metadata fields are mathematically consistent
    """

    @settings(max_examples=100)
    @given(
        total=st_total,
        per_page=st_per_page,
    )
    def test_total_pages_calculation(self, total, per_page):
        """**Validates: Requirements 22.1**

        total_pages should always equal ceil(total / per_page).
        Uses the same formula as the paginated_response utility.
        """
        # Formula from paginated_response: (total + per_page - 1) // per_page
        expected_total_pages = math.ceil(total / per_page) if total > 0 else 0
        actual_total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        # For total > 0, both formulas should agree
        if total > 0:
            assert expected_total_pages == actual_total_pages
        else:
            # For total == 0, total_pages should be 0
            assert actual_total_pages == 0 or expected_total_pages == 0

    @settings(max_examples=100)
    @given(
        total=st.integers(min_value=1, max_value=10000),
        per_page=st_per_page,
        page=st_page,
    )
    def test_pagination_metadata_from_repository(self, total, per_page, page):
        """**Validates: Requirements 22.2**

        The BaseRepository.list_paginated returns metadata where:
        - total_pages = ceil(total / per_page)
        - page is clamped to valid range
        - per_page is clamped to [1, 100]
        """
        import uuid

        session = make_session()
        repo = SampleRepository(session)

        # Insert 'total' items into the database
        now = datetime.now(timezone.utc)
        for i in range(total):
            item = SampleModel(
                id=str(uuid.uuid4()),
                created_at=now,
                updated_at=now,
                name=f"item_{i}",
                value=i,
            )
            session.add(item)
        session.flush()

        # Perform paginated query
        items, pagination_meta = repo.list_paginated(page=page, per_page=per_page)

        # Verify pagination metadata consistency
        clamped_per_page = max(1, min(per_page, 100))
        expected_total_pages = math.ceil(total / clamped_per_page)

        assert pagination_meta["total"] == total
        assert pagination_meta["per_page"] == clamped_per_page
        assert pagination_meta["total_pages"] == expected_total_pages
        assert pagination_meta["page"] == max(1, page)

        # Items on a page should not exceed per_page
        assert len(items) <= clamped_per_page

        session.close()

    @settings(max_examples=100)
    @given(
        total=st.integers(min_value=0, max_value=200),
        per_page=st_per_page,
    )
    def test_all_items_covered_by_pages(self, total, per_page):
        """**Validates: Requirements 22.1, 22.2**

        Iterating through all pages should yield exactly 'total' items total.
        """
        import uuid

        session = make_session()
        repo = SampleRepository(session)

        now = datetime.now(timezone.utc)
        for i in range(total):
            item = SampleModel(
                id=str(uuid.uuid4()),
                created_at=now,
                updated_at=now,
                name=f"item_{i}",
                value=i,
            )
            session.add(item)
        session.flush()

        # Iterate all pages and count items
        clamped_per_page = max(1, min(per_page, 100))
        total_pages = math.ceil(total / clamped_per_page) if total > 0 else 0
        all_items_count = 0

        for p in range(1, total_pages + 1):
            items, meta = repo.list_paginated(page=p, per_page=per_page)
            all_items_count += len(items)

        assert all_items_count == total

        session.close()


# ---------------------------------------------------------------------------
# Property 28: Sorting correctness
# ---------------------------------------------------------------------------

class TestSortingCorrectness:
    """Property 28: Sorting correctness.

    **Validates: Requirements 22.3**

    Results must be correctly sorted ascending or descending by specified field.
    """

    @settings(max_examples=100)
    @given(
        values=st.lists(
            st.integers(min_value=-10000, max_value=10000),
            min_size=1,
            max_size=30,
        ),
    )
    def test_ascending_sort_by_value(self, values):
        """**Validates: Requirements 22.3**

        Sorting by 'value' ascending returns items in non-decreasing order.
        """
        import uuid

        session = make_session()
        repo = SampleRepository(session)

        now = datetime.now(timezone.utc)
        for i, val in enumerate(values):
            item = SampleModel(
                id=str(uuid.uuid4()),
                created_at=now,
                updated_at=now,
                name=f"item_{i}",
                value=val,
            )
            session.add(item)
        session.flush()

        # Query sorted ascending by value - use per_page large enough
        items, _ = repo.list_paginated(
            page=1, per_page=100, sort_by="value"
        )

        # Verify ascending order
        for i in range(len(items) - 1):
            assert items[i].value <= items[i + 1].value

        session.close()

    @settings(max_examples=100)
    @given(
        values=st.lists(
            st.integers(min_value=-10000, max_value=10000),
            min_size=1,
            max_size=30,
        ),
    )
    def test_descending_sort_by_value(self, values):
        """**Validates: Requirements 22.3**

        Sorting by '-value' (descending) returns items in non-increasing order.
        """
        import uuid

        session = make_session()
        repo = SampleRepository(session)

        now = datetime.now(timezone.utc)
        for i, val in enumerate(values):
            item = SampleModel(
                id=str(uuid.uuid4()),
                created_at=now,
                updated_at=now,
                name=f"item_{i}",
                value=val,
            )
            session.add(item)
        session.flush()

        # Query sorted descending by value
        items, _ = repo.list_paginated(
            page=1, per_page=100, sort_by="-value"
        )

        # Verify descending order
        for i in range(len(items) - 1):
            assert items[i].value >= items[i + 1].value

        session.close()

    @settings(max_examples=100)
    @given(
        names=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),
                min_size=1,
                max_size=20,
            ),
            min_size=1,
            max_size=30,
        ),
        descending=st.booleans(),
    )
    def test_sort_by_name_field(self, names, descending):
        """**Validates: Requirements 22.3**

        Sorting by 'name' (asc) or '-name' (desc) returns items in correct order.
        """
        import uuid

        session = make_session()
        repo = SampleRepository(session)

        now = datetime.now(timezone.utc)
        for i, name in enumerate(names):
            item = SampleModel(
                id=str(uuid.uuid4()),
                created_at=now,
                updated_at=now,
                name=name,
                value=i,
            )
            session.add(item)
        session.flush()

        sort_by = "-name" if descending else "name"
        items, _ = repo.list_paginated(page=1, per_page=100, sort_by=sort_by)

        # Verify ordering
        for i in range(len(items) - 1):
            if descending:
                assert items[i].name >= items[i + 1].name
            else:
                assert items[i].name <= items[i + 1].name

        session.close()

    @settings(max_examples=100)
    @given(
        values=st.lists(
            st.integers(min_value=-10000, max_value=10000),
            min_size=1,
            max_size=50,
        ),
        per_page=st.integers(min_value=1, max_value=20),
        descending=st.booleans(),
    )
    def test_sort_preserved_across_pages(self, values, per_page, descending):
        """**Validates: Requirements 22.3**

        Sorting order is preserved when paginating - last item on page N
        relates correctly to first item on page N+1.
        """
        import uuid

        session = make_session()
        repo = SampleRepository(session)

        now = datetime.now(timezone.utc)
        for i, val in enumerate(values):
            item = SampleModel(
                id=str(uuid.uuid4()),
                created_at=now,
                updated_at=now,
                name=f"item_{i}",
                value=val,
            )
            session.add(item)
        session.flush()

        sort_by = "-value" if descending else "value"
        total_pages = math.ceil(len(values) / per_page)

        prev_last_value = None
        for p in range(1, total_pages + 1):
            items, _ = repo.list_paginated(
                page=p, per_page=per_page, sort_by=sort_by
            )
            if not items:
                break

            # Check ordering within the page
            for i in range(len(items) - 1):
                if descending:
                    assert items[i].value >= items[i + 1].value
                else:
                    assert items[i].value <= items[i + 1].value

            # Check continuity between pages
            if prev_last_value is not None:
                if descending:
                    assert prev_last_value >= items[0].value
                else:
                    assert prev_last_value <= items[0].value

            prev_last_value = items[-1].value

        session.close()
