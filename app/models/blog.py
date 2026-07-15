"""BlogPost model for platform content and SEO.

Validates: Requirement 15.1
- 15.1: Platform supports blog posts with categories, tags, SEO metadata,
         and draft/published workflow for content marketing.
"""

import enum

from app.extensions import db
from app.models.base import AuditMixin


class BlogPostStatus(enum.Enum):
    """Enumeration of blog post statuses."""

    draft = "draft"
    published = "published"


class BlogPost(AuditMixin, db.Model):
    """Blog post model for platform content.

    Attributes:
        title: Post title (max 255 chars).
        slug: URL-friendly unique slug (max 255 chars).
        body: Full post body content.
        author_id: FK to the user who authored the post.
        category: Post category (max 100 chars).
        tags: JSONB array of tag strings (nullable).
        featured_image_url: URL to the featured image (max 500 chars, nullable).
        seo_title: SEO-optimized title (max 255 chars, nullable).
        seo_description: SEO meta description (max 500 chars, nullable).
        status: Publication status (draft, published).
        published_at: Timestamp when the post was published (nullable).
    """

    __tablename__ = "blog_posts"

    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    category = db.Column(db.String(100), nullable=False, index=True)
    tags = db.Column(db.JSON, nullable=True)
    featured_image_url = db.Column(db.String(500), nullable=True)
    seo_title = db.Column(db.String(255), nullable=True)
    seo_description = db.Column(db.String(500), nullable=True)
    status = db.Column(
        db.Enum(BlogPostStatus, name="blog_post_status_enum"),
        nullable=False,
        default=BlogPostStatus.draft,
        index=True,
    )
    published_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<BlogPost {self.slug} ({self.status.value})>"
