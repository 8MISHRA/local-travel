"""API v1 blueprint registration.

All v1 routes are grouped under this blueprint with url_prefix=/api/v1.
Individual resource blueprints are registered as nested blueprints.

Validates: Requirement 27.1 - All endpoints prefixed with /api/v1/.
"""

from flask import Blueprint

v1_bp = Blueprint("v1", __name__, url_prefix="/api/v1")

# --- Auth blueprint ---
from app.api.v1.auth.routes import auth_bp  # noqa: E402

v1_bp.register_blueprint(auth_bp)

# --- Destinations blueprint ---
from app.api.v1.destinations.routes import destinations_bp  # noqa: E402

v1_bp.register_blueprint(destinations_bp)

# --- Packages blueprint ---
from app.api.v1.packages.routes import packages_bp  # noqa: E402

v1_bp.register_blueprint(packages_bp)

# --- Bookings blueprint ---
from app.api.v1.bookings.routes import bookings_bp  # noqa: E402

v1_bp.register_blueprint(bookings_bp)

# --- Hotels blueprint ---
from app.api.v1.hotels.routes import hotels_bp  # noqa: E402

v1_bp.register_blueprint(hotels_bp)

# --- Drivers blueprint ---
from app.api.v1.drivers.routes import drivers_bp, bookings_drivers_bp  # noqa: E402

v1_bp.register_blueprint(drivers_bp)
v1_bp.register_blueprint(bookings_drivers_bp)

# --- Scouts blueprint ---
from app.api.v1.scouts.routes import scouts_bp, bookings_scouts_bp  # noqa: E402

v1_bp.register_blueprint(scouts_bp)
v1_bp.register_blueprint(bookings_scouts_bp)

# --- Payments blueprint ---
from app.api.v1.payments.routes import payments_bp, bookings_payments_bp  # noqa: E402

v1_bp.register_blueprint(payments_bp)
v1_bp.register_blueprint(bookings_payments_bp)

# --- Health blueprint ---
from app.api.v1.health.routes import health_bp  # noqa: E402

v1_bp.register_blueprint(health_bp)

# --- Invoices blueprint (stub) ---
from app.api.v1.invoices.routes import invoices_bp  # noqa: E402

v1_bp.register_blueprint(invoices_bp)

# --- Reviews blueprint (stub) ---
from app.api.v1.reviews.routes import reviews_bp  # noqa: E402

v1_bp.register_blueprint(reviews_bp)

# --- Gallery blueprint (stub) ---
from app.api.v1.gallery.routes import gallery_bp  # noqa: E402

v1_bp.register_blueprint(gallery_bp)

# --- Blog blueprint (stub) ---
from app.api.v1.blog.routes import blog_bp  # noqa: E402

v1_bp.register_blueprint(blog_bp)

# --- Enterprise blueprint (stub) ---
from app.api.v1.enterprise.routes import enterprise_bp  # noqa: E402

v1_bp.register_blueprint(enterprise_bp)

# --- Coupons blueprint (stub) ---
from app.api.v1.coupons.routes import coupons_bp  # noqa: E402

v1_bp.register_blueprint(coupons_bp)

# --- Wishlist blueprint (stub) ---
from app.api.v1.wishlist.routes import wishlist_bp  # noqa: E402

v1_bp.register_blueprint(wishlist_bp)

# --- Notifications blueprint (stub) ---
from app.api.v1.notifications.routes import notifications_bp  # noqa: E402

v1_bp.register_blueprint(notifications_bp)

# --- Support blueprint (stub) ---
from app.api.v1.support.routes import support_bp  # noqa: E402

v1_bp.register_blueprint(support_bp)

# --- Users blueprint (stub) ---
from app.api.v1.users.routes import users_bp  # noqa: E402

v1_bp.register_blueprint(users_bp)
