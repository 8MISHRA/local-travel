"""User repository for data access operations on User model.

Validates: Requirements 1.1, 2.1
- 1.1: User registration (create_user)
- 2.1: Authentication (get_by_email for login lookup)
"""

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Repository for User model CRUD operations."""

    model_class = User

    def get_by_email(self, email):
        """Find a non-deleted user by email address.

        Args:
            email: The email address to search for.

        Returns:
            User instance if found, None otherwise.
        """
        return self.session.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None),
        ).first()

    def get_by_id(self, user_id):
        """Find a non-deleted user by ID.

        Args:
            user_id: The UUID string of the user.

        Returns:
            User instance if found, None otherwise.
        """
        return self.session.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None),
        ).first()

    def create_user(self, email, password_hash, full_name, phone, role=None):
        """Create a new user record.

        Args:
            email: User's email address.
            password_hash: Bcrypt-hashed password string.
            full_name: User's full name.
            phone: User's phone number.
            role: Optional UserRole enum value (defaults to customer).

        Returns:
            The newly created User instance (flushed, not committed).
        """
        kwargs = {
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "phone": phone,
        }
        if role is not None:
            kwargs["role"] = role

        return self.create(**kwargs)
