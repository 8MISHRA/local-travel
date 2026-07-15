"""Tests for audit action decorator.

Validates: Requirement 25.3
"""

import pytest
from unittest.mock import patch, MagicMock

from flask import g


class TestAuditAction:
    """Tests for the audit_action decorator."""

    def test_audit_action_creates_log_entry(self, app):
        """Verify audit_action creates an AuditLog record for authenticated users."""
        from app.utils.audit import audit_action

        with app.app_context():
            g.current_user_id = "user-123"
            g.current_user_role = "admin"

            with patch("app.utils.audit.db.session") as mock_session:
                mock_session.add = MagicMock()
                mock_session.commit = MagicMock()

                @audit_action("create", "package")
                def create_package(**kwargs):
                    result = MagicMock()
                    result.id = "pkg-456"
                    return result

                result = create_package()

                mock_session.add.assert_called_once()
                audit_entry = mock_session.add.call_args[0][0]
                assert audit_entry.actor_id == "user-123"
                assert audit_entry.action == "create"
                assert audit_entry.target_entity == "package"
                assert audit_entry.target_id == "pkg-456"
                mock_session.commit.assert_called_once()

    def test_audit_action_skips_unauthenticated(self, app):
        """Verify no audit log is created when no user is authenticated."""
        from app.utils.audit import audit_action

        with app.app_context():
            # Don't set g.current_user_id

            with patch("app.utils.audit.db.session") as mock_session:

                @audit_action("delete", "user")
                def delete_user(**kwargs):
                    return {"id": "user-789"}

                result = delete_user()

                mock_session.add.assert_not_called()
                assert result == {"id": "user-789"}

    def test_audit_action_extracts_id_from_dict(self, app):
        """Verify target_id extraction from dict return value."""
        from app.utils.audit import audit_action

        with app.app_context():
            g.current_user_id = "admin-1"
            g.current_user_role = "super_admin"

            with patch("app.utils.audit.db.session") as mock_session:
                mock_session.add = MagicMock()
                mock_session.commit = MagicMock()

                @audit_action("update", "destination")
                def update_destination(**kwargs):
                    return {"id": "dest-99", "name": "Varanasi"}

                update_destination()

                audit_entry = mock_session.add.call_args[0][0]
                assert audit_entry.target_id == "dest-99"

    def test_audit_action_extracts_id_from_kwargs(self, app):
        """Verify target_id extraction from kwargs when result has no id."""
        from app.utils.audit import audit_action

        with app.app_context():
            g.current_user_id = "admin-2"
            g.current_user_role = "admin"

            with patch("app.utils.audit.db.session") as mock_session:
                mock_session.add = MagicMock()
                mock_session.commit = MagicMock()

                @audit_action("delete", "booking")
                def cancel_booking(**kwargs):
                    return None

                cancel_booking(target_id="booking-100")

                audit_entry = mock_session.add.call_args[0][0]
                assert audit_entry.target_id == "booking-100"

    def test_audit_action_preserves_return_value(self, app):
        """Verify the decorator does not alter the function's return value."""
        from app.utils.audit import audit_action

        with app.app_context():
            g.current_user_id = "admin-3"
            g.current_user_role = "admin"

            with patch("app.utils.audit.db.session"):

                @audit_action("create", "hotel")
                def create_hotel(**kwargs):
                    return {"id": "hotel-1", "name": "Test Hotel"}

                result = create_hotel()
                assert result == {"id": "hotel-1", "name": "Test Hotel"}

    def test_audit_action_uses_unknown_when_no_id(self, app):
        """Verify target_id defaults to 'unknown' when it cannot be extracted."""
        from app.utils.audit import audit_action

        with app.app_context():
            g.current_user_id = "admin-4"
            g.current_user_role = "admin"

            with patch("app.utils.audit.db.session") as mock_session:
                mock_session.add = MagicMock()
                mock_session.commit = MagicMock()

                @audit_action("bulk_update", "packages")
                def bulk_operation():
                    return "done"

                bulk_operation()

                audit_entry = mock_session.add.call_args[0][0]
                assert audit_entry.target_id == "unknown"
