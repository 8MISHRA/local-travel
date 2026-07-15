"""Wishlist model for customer package favorites.

Validates: Requirement 18.1
- 18.1: Customers can save packages to a wishlist for later booking.
"""

from datetime import datetime, timezone
import uuid

from app.extensions import db


class Wishlist(db.Model):
    """Wishlist model tracking customer-saved packages.

    Each customer can save a package only once (unique constraint on
    customer_id + package_id).
    """

    __tablename__ = "wishlists"
    __table_args__ = (
        db.UniqueConstraint(
            "customer_id", "package_id", name="uq_customer_package_wishlist"
        ),
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    package_id = db.Column(
        db.String(36),
        db.ForeignKey("packages.id"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<Wishlist customer={self.customer_id} package={self.package_id}>"
