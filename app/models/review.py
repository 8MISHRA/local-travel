"""Review model for customer feedback on packages, scouts, and drivers.

Validates: Requirement 13.1
- 13.1: Customers can submit reviews with ratings (1-5) for packages, scouts,
         and drivers after completing a booking. Reviews go through moderation
         before being published.
"""

import enum

from app.extensions import db
from app.models.base import AuditMixin


class ReviewEntityType(enum.Enum):
    """Enumeration of entity types that can be reviewed."""

    package = "package"
    scout = "scout"
    driver = "driver"


class ReviewStatus(enum.Enum):
    """Enumeration of review moderation statuses."""

    pending_moderation = "pending_moderation"
    published = "published"
    rejected = "rejected"


class Review(AuditMixin, db.Model):
    """Customer review model.

    Attributes:
        customer_id: FK to the user who wrote the review.
        booking_id: FK to the associated booking.
        package_id: FK to the reviewed package.
        entity_type: Type of entity being reviewed (package, scout, driver).
        entity_id: UUID of the specific entity being reviewed.
        rating: Integer rating from 1 to 5.
        title: Optional review title (max 255 chars).
        body: Optional review body text.
        status: Moderation status (pending_moderation, published, rejected).
        rejection_reason: Optional reason if review was rejected.
    """

    __tablename__ = "reviews"

    customer_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    booking_id = db.Column(
        db.String(36),
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True,
    )
    package_id = db.Column(
        db.String(36),
        db.ForeignKey("packages.id"),
        nullable=False,
        index=True,
    )
    entity_type = db.Column(
        db.Enum(ReviewEntityType, name="review_entity_type_enum"),
        nullable=False,
    )
    entity_id = db.Column(
        db.String(36),
        nullable=False,
        index=True,
    )
    rating = db.Column(
        db.Integer,
        nullable=False,
    )
    title = db.Column(db.String(255), nullable=True)
    body = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(ReviewStatus, name="review_status_enum"),
        nullable=False,
        default=ReviewStatus.pending_moderation,
        index=True,
    )
    rejection_reason = db.Column(db.Text, nullable=True)

    # Constraints
    __table_args__ = (
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )

    def __repr__(self):
        return f"<Review {self.id} by {self.customer_id} - {self.rating}/5>"
