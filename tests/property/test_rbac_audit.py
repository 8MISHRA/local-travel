"""Property-based tests for RBAC and audit log creation.

**Validates: Requirements 4.2, 4.3, 4.4, 25.3**

Property 7: Role-based access enforcement
- For any endpoint with role restrictions, users without the required role always get 403.
- Users with the required role get access (not 403).
- Users without any token get 401.

Property 30: Audit log creation for admin operations
- When an admin performs a create/update/delete via a decorated function,
  an AuditLog entry is always created with correct actor, action, target_entity, and target_id.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta

import jwt
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Set DATABASE_URL to SQLite before any app imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.middleware.auth_middleware import auth_required
from app.models.audit_log import AuditLog
from app.utils.audit import audit_action


# --- Strategies ---

ALL_ROLES = ["guest", "customer", "scout", "driver", "vendor", "hotel_partner", "admin", "super_admin"]

role_strategy = st.sampled_from(ALL_ROLES)

# Strategy for action strings used in audit_action decorator
action_strategy = st.sampled_from(["create", "update", "delete"])

# Strategy for target_entity strings
target_entity_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
    min_size=1,
    max_size=50,
)


# --- Helpers ---

def generate_access_token(app, user_id, role):
    """Generate a valid JWT access token for testing."""
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, app.config["JWT_SECRET"], algorithm="HS256")


def make_app():
    """Create a test Flask app configured with in-memory SQLite."""
    app = create_app("testing")
    return app


# --- Property 7: Role-based access enforcement ---

class TestRoleBasedAccessEnforcement:
    """Property 7: Role-based access enforcement.

    **Validates: Requirements 4.2, 4.3, 4.4**

    For any endpoint with role restrictions:
    - Users without the required role always get 403.
    - Users with the required role get access (not 401 or 403).
    - Unauthenticated requests to protected endpoints get 401.
    """

    @given(
        allowed_roles=st.lists(
            role_strategy,
            min_size=1,
            max_size=4,
            unique=True,
        ),
        requesting_role=role_strategy,
    )
    @settings(max_examples=100)
    def test_unauthorized_role_gets_403(self, allowed_roles, requesting_role):
        """Users with a role NOT in the allowed list always receive 403.

        **Validates: Requirements 4.3**
        """
        assume(requesting_role not in allowed_roles)

        app = make_app()

        # Register a test route with role restriction
        @app.route("/test-rbac-denied")
        @auth_required(roles=allowed_roles)
        def restricted_route():
            return {"success": True, "data": None, "message": "Access granted"}, 200

        user_id = str(uuid.uuid4())
        token = generate_access_token(app, user_id, requesting_role)

        with app.test_client() as client:
            response = client.get(
                "/test-rbac-denied",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 403

    @given(
        allowed_roles=st.lists(
            role_strategy,
            min_size=1,
            max_size=4,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_authorized_role_gets_access(self, allowed_roles):
        """Users with a role IN the allowed list receive access (200, not 403).

        **Validates: Requirements 4.2**
        """
        app = make_app()

        # Pick one of the allowed roles to test
        requesting_role = allowed_roles[0]

        @app.route("/test-rbac-allowed")
        @auth_required(roles=allowed_roles)
        def allowed_route():
            return {"success": True, "data": None, "message": "Access granted"}, 200

        user_id = str(uuid.uuid4())
        token = generate_access_token(app, user_id, requesting_role)

        with app.test_client() as client:
            response = client.get(
                "/test-rbac-allowed",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200

    @given(
        allowed_roles=st.lists(
            role_strategy,
            min_size=1,
            max_size=4,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_missing_token_gets_401(self, allowed_roles):
        """Requests without an authentication token always receive 401.

        **Validates: Requirements 4.4**
        """
        app = make_app()

        @app.route("/test-rbac-no-token")
        @auth_required(roles=allowed_roles)
        def no_token_route():
            return {"success": True, "data": None, "message": "Access granted"}, 200

        with app.test_client() as client:
            response = client.get("/test-rbac-no-token")
            assert response.status_code == 401

    @given(
        allowed_roles=st.lists(
            role_strategy,
            min_size=1,
            max_size=4,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_expired_token_gets_401(self, allowed_roles):
        """Requests with an expired token always receive 401.

        **Validates: Requirements 4.4**
        """
        app = make_app()

        @app.route("/test-rbac-expired")
        @auth_required(roles=allowed_roles)
        def expired_route():
            return {"success": True, "data": None, "message": "Access granted"}, 200

        # Generate expired token
        user_id = str(uuid.uuid4())
        payload = {
            "sub": user_id,
            "role": allowed_roles[0],
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=1),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=30),
        }
        expired_token = jwt.encode(payload, app.config["JWT_SECRET"], algorithm="HS256")

        with app.test_client() as client:
            response = client.get(
                "/test-rbac-expired",
                headers={"Authorization": f"Bearer {expired_token}"},
            )
            assert response.status_code == 401

    @given(
        requesting_role=role_strategy,
    )
    @settings(max_examples=100)
    def test_no_role_restriction_allows_any_authenticated_user(self, requesting_role):
        """When no roles are specified, any authenticated user gets access.

        **Validates: Requirements 4.2**
        """
        app = make_app()

        @app.route("/test-rbac-any-role")
        @auth_required()
        def any_role_route():
            return {"success": True, "data": None, "message": "Access granted"}, 200

        user_id = str(uuid.uuid4())
        token = generate_access_token(app, user_id, requesting_role)

        with app.test_client() as client:
            response = client.get(
                "/test-rbac-any-role",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200


# --- Property 30: Audit log creation for admin operations ---

class TestAuditLogCreation:
    """Property 30: Audit log creation for admin operations.

    **Validates: Requirements 25.3**

    When an admin performs a create/update/delete via a decorated function,
    an AuditLog entry is always created with correct actor, action,
    target_entity, and target_id.
    """

    @given(
        action=action_strategy,
        target_entity=target_entity_strategy,
    )
    @settings(max_examples=100)
    def test_audit_log_created_with_correct_fields(self, action, target_entity):
        """An AuditLog entry is always created with correct actor, action, target_entity, and target_id.

        **Validates: Requirements 25.3**
        """
        app = make_app()

        with app.app_context():
            db.create_all()

            actor_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

            # Define a function decorated with audit_action
            @audit_action(action, target_entity)
            def audited_operation(**kwargs):
                """Simulates an admin operation that returns an object with an id."""
                class Result:
                    pass
                result = Result()
                result.id = target_id
                return result

            # Simulate authenticated admin context
            from flask import g
            with app.test_request_context():
                g.current_user_id = actor_id

                # Execute the audited operation
                audited_operation()

                # Verify audit log was created
                audit_entry = AuditLog.query.filter_by(
                    actor_id=actor_id,
                    action=action,
                    target_entity=target_entity,
                ).first()

                assert audit_entry is not None
                assert audit_entry.actor_id == actor_id
                assert audit_entry.action == action
                assert audit_entry.target_entity == target_entity
                assert audit_entry.target_id == target_id
                assert audit_entry.created_at is not None

            db.session.remove()
            db.drop_all()

    @given(
        action=action_strategy,
        target_entity=target_entity_strategy,
    )
    @settings(max_examples=100)
    def test_audit_log_not_created_without_authenticated_user(self, action, target_entity):
        """No AuditLog entry is created when there is no authenticated user.

        **Validates: Requirements 25.3**
        """
        app = make_app()

        with app.app_context():
            db.create_all()

            target_id = str(uuid.uuid4())

            @audit_action(action, target_entity)
            def audited_operation_no_user(**kwargs):
                class Result:
                    pass
                result = Result()
                result.id = target_id
                return result

            # Execute without setting g.current_user_id
            with app.test_request_context():
                audited_operation_no_user()

                # Verify NO audit log was created
                audit_count = AuditLog.query.count()
                assert audit_count == 0

            db.session.remove()
            db.drop_all()

    @given(
        action=action_strategy,
        target_entity=target_entity_strategy,
    )
    @settings(max_examples=100)
    def test_audit_log_extracts_target_id_from_dict_result(self, action, target_entity):
        """Audit log correctly extracts target_id from dict results.

        **Validates: Requirements 25.3**
        """
        app = make_app()

        with app.app_context():
            db.create_all()

            actor_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

            @audit_action(action, target_entity)
            def audited_operation_dict(**kwargs):
                """Returns a dict with an id field."""
                return {"id": target_id, "name": "test"}

            from flask import g
            with app.test_request_context():
                g.current_user_id = actor_id

                audited_operation_dict()

                audit_entry = AuditLog.query.filter_by(
                    actor_id=actor_id,
                    action=action,
                    target_entity=target_entity,
                ).first()

                assert audit_entry is not None
                assert audit_entry.target_id == target_id

            db.session.remove()
            db.drop_all()

    @given(
        action=action_strategy,
        target_entity=target_entity_strategy,
    )
    @settings(max_examples=100)
    def test_audit_log_uses_kwarg_target_id_as_fallback(self, action, target_entity):
        """Audit log extracts target_id from kwargs when result has no id.

        **Validates: Requirements 25.3**
        """
        app = make_app()

        with app.app_context():
            db.create_all()

            actor_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

            @audit_action(action, target_entity)
            def audited_operation_kwargs(**kwargs):
                """Returns None - target_id should be extracted from kwargs."""
                return None

            from flask import g
            with app.test_request_context():
                g.current_user_id = actor_id

                audited_operation_kwargs(target_id=target_id)

                audit_entry = AuditLog.query.filter_by(
                    actor_id=actor_id,
                    action=action,
                    target_entity=target_entity,
                ).first()

                assert audit_entry is not None
                assert audit_entry.target_id == target_id

            db.session.remove()
            db.drop_all()

    @given(
        action=action_strategy,
        target_entity=target_entity_strategy,
        admin_role=st.sampled_from(["admin", "super_admin"]),
    )
    @settings(max_examples=100)
    def test_audit_log_created_in_http_context(self, action, target_entity, admin_role):
        """Audit log is created correctly when the operation is triggered via HTTP with admin role.

        **Validates: Requirements 25.3**
        """
        app = make_app()

        with app.app_context():
            db.create_all()

            actor_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

            @audit_action(action, target_entity)
            def admin_operation(**kwargs):
                class Result:
                    pass
                result = Result()
                result.id = target_id
                return result

            # Register a test route that uses the audited function
            @app.route("/test-audit-http", methods=["POST"])
            @auth_required(roles=["admin", "super_admin"])
            def audit_http_route():
                admin_operation()
                return {"success": True, "data": None, "message": "Done"}, 200

            token = generate_access_token(app, actor_id, admin_role)

            with app.test_client() as client:
                response = client.post(
                    "/test-audit-http",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert response.status_code == 200

                # Verify audit log was created
                audit_entry = AuditLog.query.filter_by(
                    actor_id=actor_id,
                    action=action,
                    target_entity=target_entity,
                ).first()

                assert audit_entry is not None
                assert audit_entry.actor_id == actor_id
                assert audit_entry.action == action
                assert audit_entry.target_entity == target_entity
                assert audit_entry.target_id == target_id

            db.session.remove()
            db.drop_all()
