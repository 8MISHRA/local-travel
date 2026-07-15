"""Role-Based Access Control (RBAC) utilities.

Provides helper functions for role checking that can be used in services
and route handlers for fine-grained permission control.

Validates: Requirements 4.1, 4.2, 4.3
"""

from flask import g

from app.utils.response import error_response


# Supported platform roles (Requirement 4.1)
ROLES = {
    "guest",
    "customer",
    "scout",
    "driver",
    "vendor",
    "hotel_partner",
    "admin",
    "super_admin",
}

# Role hierarchy: higher-privilege roles include lower-privilege capabilities
ROLE_HIERARCHY = {
    "guest": 0,
    "customer": 1,
    "scout": 2,
    "driver": 2,
    "vendor": 2,
    "hotel_partner": 2,
    "admin": 3,
    "super_admin": 4,
}

# Convenience role groupings for common access patterns
ADMIN_ROLES = ["admin", "super_admin"]
STAFF_ROLES = ["scout", "driver", "admin", "super_admin"]
PARTNER_ROLES = ["vendor", "hotel_partner", "admin", "super_admin"]
ALL_AUTHENTICATED_ROLES = list(ROLES - {"guest"})


def is_valid_role(role):
    """Check if a role string is a recognized platform role.

    Args:
        role: Role string to validate.

    Returns:
        True if the role is valid, False otherwise.
    """
    return role in ROLES


def get_current_user_role():
    """Get the current authenticated user's role from flask.g.

    Returns:
        The role string or None if not authenticated.
    """
    return getattr(g, "current_user_role", None)


def get_current_user_id():
    """Get the current authenticated user's ID from flask.g.

    Returns:
        The user ID string or None if not authenticated.
    """
    return getattr(g, "current_user_id", None)


def has_role(required_role):
    """Check if the current user has a specific role.

    Args:
        required_role: The role to check for.

    Returns:
        True if the current user has the specified role.
    """
    current_role = get_current_user_role()
    return current_role == required_role


def has_any_role(required_roles):
    """Check if the current user has any of the specified roles.

    Args:
        required_roles: List of acceptable role strings.

    Returns:
        True if the current user's role is in the list.
    """
    current_role = get_current_user_role()
    return current_role in required_roles


def has_minimum_role(minimum_role):
    """Check if the current user's role meets a minimum privilege level.

    Uses ROLE_HIERARCHY to determine if the user's role is at or above
    the specified minimum level.

    Args:
        minimum_role: The minimum required role level.

    Returns:
        True if the current user's role level is >= the minimum.
    """
    current_role = get_current_user_role()
    if current_role is None:
        return False
    current_level = ROLE_HIERARCHY.get(current_role, 0)
    required_level = ROLE_HIERARCHY.get(minimum_role, 0)
    return current_level >= required_level


def is_admin():
    """Check if the current user is an admin or super_admin.

    Returns:
        True if the user has admin-level access.
    """
    return has_any_role(ADMIN_ROLES)


def is_super_admin():
    """Check if the current user is a super_admin.

    Returns:
        True if the user is super_admin.
    """
    return has_role("super_admin")


def is_owner_or_admin(resource_user_id):
    """Check if the current user owns the resource or is an admin.

    Useful for endpoints where users can manage their own resources
    and admins can manage any resource.

    Args:
        resource_user_id: The user_id that owns the resource.

    Returns:
        True if the current user owns the resource or is an admin.
    """
    current_user_id = get_current_user_id()
    if current_user_id == resource_user_id:
        return True
    return is_admin()


def check_permission(required_roles):
    """Check permission and return an error response if unauthorized.

    For use in service-layer code where the decorator pattern isn't suitable.

    Args:
        required_roles: List of roles that have permission.

    Returns:
        None if authorized, or an error_response tuple if unauthorized.
    """
    if not has_any_role(required_roles):
        return error_response(
            "FORBIDDEN",
            "Insufficient permissions",
            status_code=403,
        )
    return None
