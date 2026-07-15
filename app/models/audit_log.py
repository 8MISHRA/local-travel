"""AuditLog model for tracking administrative actions.

Validates: Requirement 25.3
- 25.3: Comprehensive audit trail logging all admin actions with
  actor, action type, target entity, and change details.
"""

from datetime import datetime, timezone
import uuid

from app.extensions import db


class AuditLog(db.Model):
    """Audit log model recording administrative and system actions.

    Stores a complete trail of who did what, to which entity,
    and what changed (as JSONB). Immutable once created.
    """

    __tablename__ = "audit_logs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    actor_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    action = db.Column(db.String(50), nullable=False)
    target_entity = db.Column(db.String(100), nullable=False, index=True)
    target_id = db.Column(db.String(36), nullable=False)
    changes = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.target_entity}:{self.target_id}>"
