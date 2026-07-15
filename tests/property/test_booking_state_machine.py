"""Property-based tests for booking state machine and data isolation.

**Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7**

Tests:
- Property 10: Booking state machine allows only valid transitions
- Property 11: Booking status history records every transition
- Property 12: Customer data isolation for bookings
"""

import uuid
from datetime import datetime, date, timezone

from hypothesis import given, settings, assume
from hypothesis import strategies as st

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.models.booking import BookingStatus
from app.services.booking_service import BookingStateMachine
from app.repositories.booking_repository import BookingRepository
from app.utils.exceptions import InvalidStateTransitionError


# ---------------------------------------------------------------------------
# Helpers: In-memory SQLAlchemy setup for property tests
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class FakeUser(Base):
    """Minimal user model for FK reference in tests."""

    __tablename__ = "users"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = sa.Column(sa.String(255), nullable=False, unique=True)
    password_hash = sa.Column(sa.String(255), nullable=False)
    full_name = sa.Column(sa.String(150), nullable=False)
    phone = sa.Column(sa.String(20), nullable=False)
    role = sa.Column(sa.String(20), nullable=False, default="customer")
    is_active = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    deleted_at = sa.Column(sa.DateTime, nullable=True)


class FakePackage(Base):
    """Minimal package model for FK reference in tests."""

    __tablename__ = "packages"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = sa.Column(sa.String(255), nullable=False)
    slug = sa.Column(sa.String(255), unique=True, nullable=False)
    description = sa.Column(sa.Text, nullable=False)
    destination_id = sa.Column(sa.String(36), nullable=False)
    duration_days = sa.Column(sa.Integer, nullable=False)
    duration_nights = sa.Column(sa.Integer, nullable=False)
    traveller_type = sa.Column(sa.String(50), nullable=False)
    inclusions = sa.Column(sa.JSON, nullable=False)
    exclusions = sa.Column(sa.JSON, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)
    featured_image_url = sa.Column(sa.String(500), nullable=True)
    average_rating = sa.Column(sa.Numeric(3, 2), default=0.00)
    total_reviews = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    deleted_at = sa.Column(sa.DateTime, nullable=True)


class FakeHotel(Base):
    """Minimal hotel model for FK reference."""

    __tablename__ = "hotels"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = sa.Column(sa.String(255), nullable=False)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    deleted_at = sa.Column(sa.DateTime, nullable=True)


class FakeRoomType(Base):
    """Minimal room type model for FK reference."""

    __tablename__ = "room_types"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = sa.Column(sa.String(36), sa.ForeignKey("hotels.id"), nullable=False)
    name = sa.Column(sa.String(100), nullable=False)


class FakeCoupon(Base):
    """Minimal coupon model for FK reference."""

    __tablename__ = "coupons"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = sa.Column(sa.String(50), unique=True, nullable=False)


class FakeBooking(Base):
    """Booking model mirroring the production schema for in-memory testing."""

    __tablename__ = "bookings"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_number = sa.Column(sa.String(20), unique=True, nullable=False)
    customer_id = sa.Column(
        sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True
    )
    package_id = sa.Column(
        sa.String(36), sa.ForeignKey("packages.id"), nullable=False
    )
    status = sa.Column(
        sa.Enum(BookingStatus, name="booking_status_enum"),
        nullable=False,
        default=BookingStatus.draft,
    )
    travel_start_date = sa.Column(sa.Date, nullable=False)
    travel_end_date = sa.Column(sa.Date, nullable=False)
    num_travellers = sa.Column(sa.Integer, nullable=False)
    traveller_type = sa.Column(sa.String(50), nullable=False)
    hotel_preference_id = sa.Column(sa.String(36), nullable=True)
    room_type_id = sa.Column(sa.String(36), nullable=True)
    transport_preferences = sa.Column(sa.JSON, nullable=True)
    add_ons = sa.Column(sa.JSON, nullable=True)
    subtotal = sa.Column(sa.Numeric(12, 2), nullable=True)
    discount_amount = sa.Column(sa.Numeric(12, 2), default=0.00)
    tax_amount = sa.Column(sa.Numeric(12, 2), nullable=True)
    total_amount = sa.Column(sa.Numeric(12, 2), nullable=True)
    coupon_id = sa.Column(sa.String(36), nullable=True)
    special_requests = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    deleted_at = sa.Column(sa.DateTime, nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = datetime.now(timezone.utc)


class FakeBookingStatusHistory(Base):
    """BookingStatusHistory model for in-memory testing."""

    __tablename__ = "booking_status_history"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = sa.Column(
        sa.String(36), sa.ForeignKey("bookings.id"), nullable=False, index=True
    )
    from_status = sa.Column(sa.String(30), nullable=True)
    to_status = sa.Column(sa.String(30), nullable=False)
    changed_by = sa.Column(
        sa.String(36), sa.ForeignKey("users.id"), nullable=False
    )
    notes = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(
        sa.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


def make_session():
    """Create an in-memory SQLite session with all required tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def create_user(session, email=None):
    """Create a user record and return it."""
    now = datetime.now(timezone.utc)
    user_id = str(uuid.uuid4())
    user = FakeUser(
        id=user_id,
        email=email or f"user_{user_id[:8]}@test.com",
        password_hash="hashed_pw",
        full_name="Test User",
        phone="1234567890",
        role="customer",
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.flush()
    return user


def create_package(session):
    """Create a package record and return it."""
    now = datetime.now(timezone.utc)
    pkg_id = str(uuid.uuid4())
    pkg = FakePackage(
        id=pkg_id,
        title=f"Package {pkg_id[:8]}",
        slug=f"pkg-{pkg_id[:8]}",
        description="Test package",
        destination_id=str(uuid.uuid4()),
        duration_days=3,
        duration_nights=2,
        traveller_type="solo",
        inclusions=["breakfast"],
        exclusions=["flights"],
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(pkg)
    session.flush()
    return pkg


def create_booking(session, customer_id, package_id, status=BookingStatus.draft):
    """Create a booking record with given status."""
    now = datetime.now(timezone.utc)
    booking_id = str(uuid.uuid4())
    booking = FakeBooking(
        id=booking_id,
        booking_number=f"BK-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer_id,
        package_id=package_id,
        status=status,
        travel_start_date=date(2025, 3, 1),
        travel_end_date=date(2025, 3, 5),
        num_travellers=2,
        traveller_type="couple",
        created_at=now,
        updated_at=now,
    )
    session.add(booking)
    session.flush()
    return booking


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

st_booking_status = st.sampled_from(list(BookingStatus))

# All possible (from, to) status pairs
st_status_pair = st.tuples(st_booking_status, st_booking_status)

# Number of bookings per customer for isolation tests
st_num_bookings = st.integers(min_value=0, max_value=8)

# Number of customers
st_num_customers = st.integers(min_value=2, max_value=5)


# ---------------------------------------------------------------------------
# Property 10: Booking state machine allows only valid transitions
# ---------------------------------------------------------------------------

class TestBookingStateMachineTransitions:
    """Property 10: Booking state machine allows only valid transitions.

    **Validates: Requirements 7.3, 7.4, 7.5**

    For any (current_status, target_status) pair, only transitions in the
    TRANSITIONS dict succeed. Invalid transitions always raise
    InvalidStateTransitionError.
    """

    @settings(max_examples=100)
    @given(
        current_status=st_booking_status,
        target_status=st_booking_status,
    )
    def test_valid_transitions_succeed_invalid_raise(
        self, current_status, target_status
    ):
        """**Validates: Requirements 7.3, 7.4, 7.5**

        For any pair of booking statuses, if the target is in
        TRANSITIONS[current], the transition succeeds. Otherwise,
        InvalidStateTransitionError is raised.
        """
        session = make_session()
        user = create_user(session)
        pkg = create_package(session)
        booking = create_booking(session, user.id, pkg.id, status=current_status)
        session.commit()

        state_machine = BookingStateMachine()
        repo = BookingRepository(session)
        # Override model classes so the repository operates on our fake models
        repo.model_class = FakeBooking

        allowed = state_machine.TRANSITIONS.get(current_status, [])
        is_valid = target_status in allowed

        if is_valid:
            # Valid transition should succeed without raising
            result = state_machine.transition(
                booking=booking,
                target_status=target_status,
                changed_by=user.id,
                repo=repo,
            )
            assert result.status == target_status
        else:
            # Invalid transition must raise InvalidStateTransitionError
            raised = False
            try:
                state_machine.transition(
                    booking=booking,
                    target_status=target_status,
                    changed_by=user.id,
                    repo=repo,
                )
            except InvalidStateTransitionError:
                raised = True
            assert raised, (
                f"Expected InvalidStateTransitionError for {current_status.value} → "
                f"{target_status.value}, but no exception was raised."
            )

        session.close()

    @settings(max_examples=100)
    @given(current_status=st_booking_status)
    def test_can_transition_consistent_with_transitions_dict(self, current_status):
        """**Validates: Requirements 7.4**

        can_transition must return True for exactly the statuses listed
        in TRANSITIONS[current_status] and False for all others.
        """
        state_machine = BookingStateMachine()
        allowed = state_machine.TRANSITIONS.get(current_status, [])

        for target in BookingStatus:
            result = state_machine.can_transition(current_status, target)
            if target in allowed:
                assert result is True, (
                    f"can_transition({current_status.value}, {target.value}) "
                    f"should be True"
                )
            else:
                assert result is False, (
                    f"can_transition({current_status.value}, {target.value}) "
                    f"should be False"
                )

    @settings(max_examples=100)
    @given(
        transitions=st.lists(
            st_booking_status,
            min_size=1,
            max_size=6,
        ),
    )
    def test_sequential_transitions_follow_allowed_paths(self, transitions):
        """**Validates: Requirements 7.4**

        Starting from draft, attempting a sequence of transitions should
        succeed only when each step is valid according to TRANSITIONS.
        Any invalid step should raise InvalidStateTransitionError, and the
        booking status should remain unchanged after the failed attempt.
        """
        session = make_session()
        user = create_user(session)
        pkg = create_package(session)
        booking = create_booking(session, user.id, pkg.id, status=BookingStatus.draft)
        session.commit()

        state_machine = BookingStateMachine()
        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        current = BookingStatus.draft
        for target in transitions:
            allowed = state_machine.TRANSITIONS.get(current, [])
            if target in allowed:
                state_machine.transition(
                    booking=booking,
                    target_status=target,
                    changed_by=user.id,
                    repo=repo,
                )
                current = target
                assert booking.status == current
            else:
                try:
                    state_machine.transition(
                        booking=booking,
                        target_status=target,
                        changed_by=user.id,
                        repo=repo,
                    )
                    # Should not reach here
                    assert False, "Expected InvalidStateTransitionError"
                except InvalidStateTransitionError:
                    # Status should remain unchanged after failed transition
                    assert booking.status == current

        session.close()


# ---------------------------------------------------------------------------
# Property 11: Booking status history records every transition
# ---------------------------------------------------------------------------

class TestBookingStatusHistoryRecording:
    """Property 11: Booking status history records every transition.

    **Validates: Requirements 7.6**

    After every successful transition, a BookingStatusHistory record is
    created with correct from_status, to_status, and changed_by.
    """

    @settings(max_examples=100)
    @given(
        current_status=st_booking_status,
        target_status=st_booking_status,
    )
    def test_successful_transition_creates_history_record(
        self, current_status, target_status
    ):
        """**Validates: Requirements 7.6**

        After a successful transition, exactly one new BookingStatusHistory
        record is created with the correct from_status, to_status, and
        changed_by values.
        """
        state_machine = BookingStateMachine()
        allowed = state_machine.TRANSITIONS.get(current_status, [])
        assume(target_status in allowed)

        session = make_session()
        user = create_user(session)
        pkg = create_package(session)
        booking = create_booking(session, user.id, pkg.id, status=current_status)
        session.commit()

        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        # Count existing history records before transition
        history_before = session.query(FakeBookingStatusHistory).filter(
            FakeBookingStatusHistory.booking_id == booking.id
        ).count()

        state_machine.transition(
            booking=booking,
            target_status=target_status,
            changed_by=user.id,
            repo=repo,
        )
        session.flush()

        # Check new history record was created
        history_after = session.query(FakeBookingStatusHistory).filter(
            FakeBookingStatusHistory.booking_id == booking.id
        ).all()

        assert len(history_after) == history_before + 1

        # Verify the latest record has correct values
        latest = history_after[-1]
        assert latest.from_status == current_status.value
        assert latest.to_status == target_status.value
        assert latest.changed_by == user.id

        session.close()

    @settings(max_examples=100)
    @given(
        path=st.lists(
            st_booking_status,
            min_size=1,
            max_size=5,
        ),
    )
    def test_multiple_transitions_create_ordered_history(self, path):
        """**Validates: Requirements 7.6**

        After a sequence of successful transitions starting from draft,
        the history table contains one record per transition, each with
        the correct from/to status pair in order.
        """
        session = make_session()
        user = create_user(session)
        pkg = create_package(session)
        booking = create_booking(session, user.id, pkg.id, status=BookingStatus.draft)
        session.commit()

        state_machine = BookingStateMachine()
        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        # Build a list of successful transitions
        successful_transitions = []
        current = BookingStatus.draft
        for target in path:
            allowed = state_machine.TRANSITIONS.get(current, [])
            if target in allowed:
                state_machine.transition(
                    booking=booking,
                    target_status=target,
                    changed_by=user.id,
                    repo=repo,
                )
                successful_transitions.append((current.value, target.value))
                current = target

        session.flush()

        # Verify history records match successful transitions
        history = session.query(FakeBookingStatusHistory).filter(
            FakeBookingStatusHistory.booking_id == booking.id
        ).order_by(FakeBookingStatusHistory.created_at).all()

        assert len(history) == len(successful_transitions)

        for record, (expected_from, expected_to) in zip(history, successful_transitions):
            assert record.from_status == expected_from
            assert record.to_status == expected_to
            assert record.changed_by == user.id

        session.close()

    @settings(max_examples=100)
    @given(
        current_status=st_booking_status,
        target_status=st_booking_status,
    )
    def test_failed_transition_does_not_create_history(
        self, current_status, target_status
    ):
        """**Validates: Requirements 7.6**

        When a transition fails (InvalidStateTransitionError), no
        BookingStatusHistory record should be created.
        """
        state_machine = BookingStateMachine()
        allowed = state_machine.TRANSITIONS.get(current_status, [])
        assume(target_status not in allowed)

        session = make_session()
        user = create_user(session)
        pkg = create_package(session)
        booking = create_booking(session, user.id, pkg.id, status=current_status)
        session.commit()

        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        history_before = session.query(FakeBookingStatusHistory).filter(
            FakeBookingStatusHistory.booking_id == booking.id
        ).count()

        try:
            state_machine.transition(
                booking=booking,
                target_status=target_status,
                changed_by=user.id,
                repo=repo,
            )
        except InvalidStateTransitionError:
            pass

        history_after = session.query(FakeBookingStatusHistory).filter(
            FakeBookingStatusHistory.booking_id == booking.id
        ).count()

        # No new history record should have been created
        assert history_after == history_before

        session.close()


# ---------------------------------------------------------------------------
# Property 12: Customer data isolation for bookings
# ---------------------------------------------------------------------------

class TestCustomerDataIsolation:
    """Property 12: Customer data isolation for bookings.

    **Validates: Requirements 7.7**

    A customer's booking listing never contains bookings belonging to
    other customers.
    """

    @settings(max_examples=100)
    @given(
        customer_bookings=st.lists(st_num_bookings, min_size=2, max_size=5),
    )
    def test_listing_only_returns_own_bookings(self, customer_bookings):
        """**Validates: Requirements 7.7**

        For multiple customers each with varying numbers of bookings,
        list_for_customer for any customer returns ONLY that customer's
        bookings and never another customer's.
        """
        session = make_session()
        pkg = create_package(session)

        # Create multiple customers with their bookings
        customers = []
        customer_booking_ids = {}

        for num_bookings in customer_bookings:
            customer = create_user(session)
            customers.append(customer)
            booking_ids = set()

            for _ in range(num_bookings):
                booking = create_booking(session, customer.id, pkg.id)
                booking_ids.add(booking.id)

            customer_booking_ids[customer.id] = booking_ids

        session.commit()

        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        # For each customer, verify isolation
        for customer in customers:
            items, meta = repo.list_for_customer(
                customer_id=customer.id, page=1, per_page=100
            )

            returned_ids = {item.id for item in items}
            expected_ids = customer_booking_ids[customer.id]

            # Property: returned bookings belong ONLY to this customer
            assert returned_ids == expected_ids, (
                f"Customer {customer.id} should see {len(expected_ids)} bookings "
                f"but got {len(returned_ids)}"
            )

            # Verify no other customer's bookings appear
            other_ids = set()
            for cid, bids in customer_booking_ids.items():
                if cid != customer.id:
                    other_ids.update(bids)

            assert returned_ids.isdisjoint(other_ids), (
                "Customer listing contains bookings from other customers!"
            )

            # Metadata total should match
            assert meta["total"] == len(expected_ids)

        session.close()

    @settings(max_examples=100)
    @given(
        num_other_bookings=st.integers(min_value=1, max_value=10),
    )
    def test_empty_customer_sees_no_bookings(self, num_other_bookings):
        """**Validates: Requirements 7.7**

        A customer with no bookings should see an empty listing even when
        other customers have bookings in the system.
        """
        session = make_session()
        pkg = create_package(session)

        # Create the target customer (no bookings)
        target_customer = create_user(session)

        # Create another customer with bookings
        other_customer = create_user(session)
        for _ in range(num_other_bookings):
            create_booking(session, other_customer.id, pkg.id)

        session.commit()

        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        items, meta = repo.list_for_customer(
            customer_id=target_customer.id, page=1, per_page=100
        )

        assert len(items) == 0
        assert meta["total"] == 0

        session.close()

    @settings(max_examples=100)
    @given(
        num_own_bookings=st.integers(min_value=1, max_value=8),
        num_other_bookings=st.integers(min_value=1, max_value=8),
        status_filter=st.one_of(st.none(), st_booking_status),
    )
    def test_status_filter_preserves_isolation(
        self, num_own_bookings, num_other_bookings, status_filter
    ):
        """**Validates: Requirements 7.7**

        Even when filtering by status, a customer's listing never includes
        another customer's bookings.
        """
        session = make_session()
        pkg = create_package(session)

        # Customer A (target)
        customer_a = create_user(session)
        statuses_a = list(BookingStatus)
        for i in range(num_own_bookings):
            status = statuses_a[i % len(statuses_a)]
            create_booking(session, customer_a.id, pkg.id, status=status)

        # Customer B (other)
        customer_b = create_user(session)
        for i in range(num_other_bookings):
            status = statuses_a[i % len(statuses_a)]
            create_booking(session, customer_b.id, pkg.id, status=status)

        session.commit()

        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        items, meta = repo.list_for_customer(
            customer_id=customer_a.id,
            page=1,
            per_page=100,
            status_filter=status_filter,
        )

        # Property: ALL returned bookings belong to customer A
        for item in items:
            assert item.customer_id == customer_a.id

        # If filtering by status, verify filter is also applied
        if status_filter is not None:
            for item in items:
                assert item.status == status_filter

        session.close()

    @settings(max_examples=100)
    @given(
        num_customers=st.integers(min_value=2, max_value=4),
        bookings_per_customer=st.integers(min_value=1, max_value=5),
    )
    def test_total_count_matches_customer_bookings_only(
        self, num_customers, bookings_per_customer
    ):
        """**Validates: Requirements 7.7**

        The pagination total for a customer's listing equals exactly
        the number of bookings they own, not the total in the system.
        """
        session = make_session()
        pkg = create_package(session)

        customers = []
        for _ in range(num_customers):
            customer = create_user(session)
            customers.append(customer)
            for _ in range(bookings_per_customer):
                create_booking(session, customer.id, pkg.id)

        session.commit()

        repo = BookingRepository(session)
        repo.model_class = FakeBooking

        total_bookings_in_system = num_customers * bookings_per_customer

        for customer in customers:
            items, meta = repo.list_for_customer(
                customer_id=customer.id, page=1, per_page=100
            )

            # Each customer should see only their own count
            assert meta["total"] == bookings_per_customer
            assert len(items) == bookings_per_customer

            # System total is larger than individual
            assert total_bookings_in_system > bookings_per_customer

        session.close()
