"""Audit action decorator for recording admin operations.

Provides the `audit_action` decorator that automatically creates
AuditLog entries when admin operations complete successfully.

Validates: Requirement 25.3
- 25.3: Records audit log entry with actor, action, target entity,
  target identifier, and timestamp for admin create/update/delete operations.
"""

from functools import wraps

from flask import g

from app.extensions import db
from app.models.audit_log import AuditLog


def audit_action(action, target_entity):
    """Decorator that records an audit log entry after a successful operation.

    Captures the actor (from g.current_user_id), the action performed,
    the target entity type, and attempts to extract the target_id from
    the function's return value or keyword arguments.

    Only records when there is an authenticated user (g.current_user_id exists).

    Args:
        action: A string describing the action (e.g., "create", "update", "delete").
        target_entity: A string identifying the entity type (e.g., "package", "user").

    Returns:
        Decorated function that logs audit entries on success.

    Usage:
        @audit_action("create", "package")
        def create_package(**kwargs):
            ...
            return new_package

        @audit_action("delete", "user")
        def delete_user(user_id=None, **kwargs):
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Capture before-state if available via kwargs
            changes_before = kwargs.pop("_audit_before", None)

            result = f(*args, **kwargs)

            # Only record audit if there's an authenticated user
            actor_id = getattr(g, "current_user_id", None)
            if actor_id is None:
                return result

            # Extract target_id from result or kwargs
            target_id = _extract_target_id(result, kwargs)

            # Build changes dict if before/after data available
            changes = None
            changes_after = kwargs.get("_audit_after", None)
            if changes_before is not None or changes_after is not None:
                changes = {}
                if changes_before is not None:
                    changes["before"] = changes_before
                if changes_after is not None:
                    changes["after"] = changes_after

            audit_entry = AuditLog(
                actor_id=actor_id,
                action=action,
                target_entity=target_entity,
                target_id=str(target_id) if target_id else "unknown",
                changes=changes,
            )
            db.session.add(audit_entry)
            db.session.commit()

            return result

        return wrapper

    return decorator


def _extract_target_id(result, kwargs):
    """Extract the target ID from the function result or keyword arguments.

    Checks in order:
    1. result.id attribute (e.g., SQLAlchemy model instance)
    2. result["id"] key (e.g., dict response)
    3. kwargs with common ID parameter names

    Args:
        result: The return value of the decorated function.
        kwargs: The keyword arguments passed to the decorated function.

    Returns:
        The extracted target ID or None.
    """
    # Try getting id from result object
    if result is not None:
        if hasattr(result, "id"):
            return result.id
        if isinstance(result, dict) and "id" in result:
            return result["id"]

    # Try common kwarg names for ID
    for key in ("target_id", "id", "entity_id"):
        if key in kwargs:
            return kwargs[key]

    return None
