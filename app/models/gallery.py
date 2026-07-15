"""GalleryImage model for media assets associated with packages, destinations, and hotels.

Validates: Requirement 14.1
- 14.1: Platform supports image galleries for packages, destinations, and hotels
         with metadata including dimensions, alt text, and display ordering.
"""

import enum
import uuid
from datetime import datetime, timezone

from app.extensions import db


class GalleryEntityType(enum.Enum):
    """Enumeration of entity types that can have gallery images."""

    package = "package"
    destination = "destination"
    hotel = "hotel"


class GalleryImage(db.Model):
    """Gallery image model for media assets.

    Attributes:
        entity_type: Type of entity this image belongs to (package, destination, hotel).
        entity_id: UUID of the specific entity.
        filename: Original filename (max 255 chars).
        file_size: File size in bytes.
        mime_type: MIME type of the image (max 50 chars).
        width: Image width in pixels (nullable).
        height: Image height in pixels (nullable).
        alt_text: Accessibility alt text (max 255 chars, nullable).
        display_order: Order for display (default 0).
        storage_url: URL to the stored image file (max 500 chars).
        created_at: Timestamp of record creation (UTC).
    """

    __tablename__ = "gallery_images"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    entity_type = db.Column(
        db.Enum(GalleryEntityType, name="gallery_entity_type_enum"),
        nullable=False,
        index=True,
    )
    entity_id = db.Column(
        db.String(36),
        nullable=False,
        index=True,
    )
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(50), nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    alt_text = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    storage_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<GalleryImage {self.filename} ({self.entity_type.value}/{self.entity_id})>"
