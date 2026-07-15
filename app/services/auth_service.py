"""Authentication service handling registration, login, and token management.

Validates: Requirements 1.1, 1.3, 1.5, 2.1, 2.3, 2.4, 2.5
- 1.1: Registration creates Customer account, returns token pair
- 1.3: Password hashed with bcrypt before storage
- 1.5: Minimum password length of 8 characters
- 2.1: Login returns Access_Token + Refresh_Token
- 2.3: Refresh token rotation (issue new pair, invalidate old)
- 2.4: Expired/invalid refresh token returns 401
- 2.5: Logout invalidates current refresh token
"""

import hashlib
import uuid
from datetime import datetime, timezone

import bcrypt
import jwt
from flask import current_app

from app.extensions import db
from app.models.user import RefreshToken, User
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import ConflictError, UnauthorizedError, ValidationError


class AuthService:
    """Service layer for authentication operations."""

    def __init__(self):
        self.user_repo = UserRepository(db.session)

    def register(self, email, password, full_name, phone):
        """Register a new user account.

        Validates inputs, hashes the password with bcrypt, creates the user,
        and generates an access/refresh token pair.

        Args:
            email: User's email address.
            password: Plaintext password (must be >= 8 characters).
            full_name: User's full name.
            phone: User's phone number.

        Returns:
            Dict with access_token, refresh_token, and user data.

        Raises:
            ValidationError: If password is too short.
            ConflictError: If email already exists.
        """
        # Validate password length (Requirement 1.5)
        if len(password) < 8:
            raise ValidationError(
                message="Password must be at least 8 characters long.",
                details={"password": ["Password must be at least 8 characters long."]},
            )

        # Check for duplicate email (Requirement 1.2 - handled in route as 409)
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ConflictError(
                message="An account with this email already exists.",
                details={"email": ["An account with this email already exists."]},
            )

        # Hash password with bcrypt (Requirement 1.3)
        password_hash = self._hash_password(password)

        # Create user (Requirement 1.1)
        user = self.user_repo.create_user(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
        )
        db.session.flush()

        # Generate token pair
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)

        # Store refresh token hash in database
        self.store_refresh_token(user.id, refresh_token)

        db.session.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": self._serialize_user(user),
        }

    def login(self, email, password):
        """Authenticate a user with email and password.

        Finds the user by email, verifies the password, and generates
        a new access/refresh token pair.

        Args:
            email: User's email address.
            password: Plaintext password to verify.

        Returns:
            Dict with access_token, refresh_token, and user data.

        Raises:
            UnauthorizedError: If credentials are invalid (generic message
                per Requirement 2.2 - does not reveal which field is wrong).
        """
        # Find user by email
        user = self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedError(message="Invalid email or password.")

        # Verify password
        if not self._verify_password(password, user.password_hash):
            raise UnauthorizedError(message="Invalid email or password.")

        # Check if user is active
        if not user.is_active:
            raise UnauthorizedError(message="Account is deactivated.")

        # Generate token pair
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)

        # Store refresh token hash
        self.store_refresh_token(user.id, refresh_token)

        db.session.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": self._serialize_user(user),
        }

    def refresh_tokens(self, refresh_token_str):
        """Rotate refresh token: validate old token, issue new pair, revoke old.

        Validates: Requirement 2.3 - Issue new Access_Token and Refresh_Token,
        invalidate old Refresh_Token.
        Validates: Requirement 2.4 - Reject expired/invalid tokens with 401.

        Steps:
            1. Decode the JWT (validates signature, checks type=="refresh")
            2. Hash the token (SHA-256) and look up in refresh_tokens table
            3. Verify record exists, is not revoked, and not expired
            4. Revoke the old token record
            5. Find the user, generate new access+refresh token pair
            6. Store the new refresh token hash
            7. Return new tokens + user data

        Args:
            refresh_token_str: The raw JWT refresh token string.

        Returns:
            Dict with access_token, refresh_token, and user data.

        Raises:
            UnauthorizedError: If token is invalid, expired, or revoked.
        """
        # Step 1: Decode the JWT
        try:
            payload = jwt.decode(
                refresh_token_str,
                current_app.config["JWT_SECRET"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError(message="Refresh token has expired.")
        except jwt.InvalidTokenError:
            raise UnauthorizedError(message="Invalid refresh token.")

        # Verify token type
        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="Invalid refresh token.")

        # Step 2: Hash the token and look up in database
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()
        token_record = db.session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
        ).first()

        # Step 3: Verify record exists and is valid
        if not token_record:
            raise UnauthorizedError(message="Invalid refresh token.")

        if token_record.is_revoked:
            raise UnauthorizedError(message="Refresh token has been revoked.")

        if token_record.is_expired:
            raise UnauthorizedError(message="Refresh token has expired.")

        # Step 4: Revoke the old token
        token_record.revoke()

        # Step 5: Find the user
        user = self.user_repo.get_by_id(payload["sub"])
        if not user:
            raise UnauthorizedError(message="User not found.")

        if not user.is_active:
            raise UnauthorizedError(message="Account is deactivated.")

        # Generate new token pair
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)

        # Step 6: Store the new refresh token hash
        self.store_refresh_token(user.id, refresh_token)

        db.session.commit()

        # Step 7: Return new tokens + user data
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": self._serialize_user(user),
        }

    def logout(self, refresh_token_str):
        """Invalidate a refresh token (logout).

        Validates: Requirement 2.5 - Logout invalidates current Refresh_Token.

        Steps:
            1. Decode the refresh token JWT
            2. Hash the token (SHA-256)
            3. Find the token record in the database
            4. Revoke it (set is_revoked=True)
            5. Commit

        Args:
            refresh_token_str: The raw JWT refresh token string.

        Raises:
            UnauthorizedError: If token is invalid or not found.
        """
        # Step 1: Decode the JWT
        try:
            payload = jwt.decode(
                refresh_token_str,
                current_app.config["JWT_SECRET"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
        except jwt.ExpiredSignatureError:
            # Even if expired, we can still try to revoke it
            # Re-decode without verification to get the token hash
            try:
                payload = jwt.decode(
                    refresh_token_str,
                    current_app.config["JWT_SECRET"],
                    algorithms=[current_app.config["JWT_ALGORITHM"]],
                    options={"verify_exp": False},
                )
            except jwt.InvalidTokenError:
                raise UnauthorizedError(message="Invalid refresh token.")
        except jwt.InvalidTokenError:
            raise UnauthorizedError(message="Invalid refresh token.")

        # Verify token type
        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="Invalid refresh token.")

        # Step 2: Hash the token
        token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()

        # Step 3: Find the token record
        token_record = db.session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
        ).first()

        if not token_record:
            raise UnauthorizedError(message="Invalid refresh token.")

        # Step 4: Revoke it
        token_record.revoke()

        # Step 5: Commit
        db.session.commit()

    def generate_access_token(self, user):
        """Generate a short-lived JWT access token.

        Payload structure (per design doc):
            sub: user_id
            role: user role
            iat: issued at
            exp: expiration (15 min from now)
            type: "access"

        Args:
            user: User model instance.

        Returns:
            Encoded JWT string.
        """
        now = datetime.now(timezone.utc)
        expiry = now + current_app.config["JWT_ACCESS_EXPIRY"]

        payload = {
            "sub": user.id,
            "role": user.role.value,
            "iat": now,
            "exp": expiry,
            "type": "access",
        }

        return jwt.encode(
            payload,
            current_app.config["JWT_SECRET"],
            algorithm=current_app.config["JWT_ALGORITHM"],
        )

    def generate_refresh_token(self, user):
        """Generate a long-lived JWT refresh token.

        Payload structure (per design doc):
            sub: user_id
            jti: unique token ID (for revocation tracking)
            iat: issued at
            exp: expiration (7 days from now)
            type: "refresh"

        Args:
            user: User model instance.

        Returns:
            Encoded JWT string.
        """
        now = datetime.now(timezone.utc)
        expiry = now + current_app.config["JWT_REFRESH_EXPIRY"]
        jti = str(uuid.uuid4())

        payload = {
            "sub": user.id,
            "jti": jti,
            "iat": now,
            "exp": expiry,
            "type": "refresh",
        }

        return jwt.encode(
            payload,
            current_app.config["JWT_SECRET"],
            algorithm=current_app.config["JWT_ALGORITHM"],
        )

    def store_refresh_token(self, user_id, refresh_token):
        """Store a hashed refresh token in the database.

        The token is stored as a SHA-256 hash for security. The original
        token is never persisted.

        Args:
            user_id: UUID of the user who owns the token.
            refresh_token: The raw JWT refresh token string.
        """
        # Decode to get expiry
        payload = jwt.decode(
            refresh_token,
            current_app.config["JWT_SECRET"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )

        # Hash the token for storage
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        # Create refresh token record
        refresh_token_record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
        db.session.add(refresh_token_record)
        db.session.flush()

    def _hash_password(self, password):
        """Hash a plaintext password using bcrypt.

        Args:
            password: Plaintext password string.

        Returns:
            Bcrypt hash string.
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password, password_hash):
        """Verify a plaintext password against a bcrypt hash.

        Args:
            password: Plaintext password to check.
            password_hash: Stored bcrypt hash.

        Returns:
            True if the password matches, False otherwise.
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )

    def _serialize_user(self, user):
        """Serialize a User instance for API response.

        Args:
            user: User model instance.

        Returns:
            Dict with user fields (excluding password_hash).
        """
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
