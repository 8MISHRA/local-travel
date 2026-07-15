"""Middleware package.

Provides authentication, authorization, rate limiting, and request processing middleware.
"""

from app.middleware.auth_middleware import auth_required
from app.middleware.rate_limiter import (
    rate_limit_login,
    rate_limit_register,
    register_rate_limit_handler,
)
from app.middleware.rbac_middleware import (
    ADMIN_ROLES,
    ALL_AUTHENTICATED_ROLES,
    PARTNER_ROLES,
    ROLES,
    STAFF_ROLES,
    check_permission,
    get_current_user_id,
    get_current_user_role,
    has_any_role,
    has_minimum_role,
    has_role,
    is_admin,
    is_owner_or_admin,
    is_super_admin,
    is_valid_role,
)

__all__ = [
    "auth_required",
    "rate_limit_login",
    "rate_limit_register",
    "register_rate_limit_handler",
    "ADMIN_ROLES",
    "ALL_AUTHENTICATED_ROLES",
    "PARTNER_ROLES",
    "ROLES",
    "STAFF_ROLES",
    "check_permission",
    "get_current_user_id",
    "get_current_user_role",
    "has_any_role",
    "has_minimum_role",
    "has_role",
    "is_admin",
    "is_owner_or_admin",
    "is_super_admin",
    "is_valid_role",
]
