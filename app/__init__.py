"""Flask application factory.

Creates and configures the Flask app, initializes extensions,
registers blueprints, and sets up global error handlers.

Validates: Requirement 27.1 - All endpoints prefixed with /api/v1/.
Validates: Requirement 26.3 - CORS headers configured for specified origins.
Validates: Requirement 26.5 - Secure, httpOnly flags on authentication cookies.
"""

import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.config import config_by_name


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration environment name. If not provided,
            reads from FLASK_ENV environment variable (default: 'development').

    Returns:
        Configured Flask application instance.
    """
    # Load .env file for local development
    load_dotenv()

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions
    _init_extensions(app)

    # Configure CORS with allowed origins from config (Requirement 26.3)
    CORS(
        app,
        origins=app.config.get("ALLOWED_ORIGINS", ["*"]),
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        supports_credentials=True,
    )

    # Configure secure session cookies (Requirement 26.5)
    app.config.setdefault("SESSION_COOKIE_SECURE", not app.config.get("DEBUG", False))
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    if app.config.get("SESSION_COOKIE_SAMESITE") is None:
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Register request logging middleware (Requirements 25.1, 25.2)
    from app.middleware.request_logger import init_request_logging

    init_request_logging(app)

    # Register blueprints
    _register_blueprints(app)

    # Set up error handlers
    _register_error_handlers(app)

    # Register security headers middleware
    _register_security_headers(app)

    return app


def _init_extensions(app):
    """Initialize Flask extensions with the app instance."""
    from app.extensions import db, ma, migrate, limiter

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Import all models so Alembic can detect them for auto-generation
    import app.models  # noqa: F401


def _register_blueprints(app):
    """Register API blueprints with the app.

    All v1 routes are registered under the /api/v1 prefix
    (Requirement 27.1).
    """
    from app.api.v1 import v1_bp

    app.register_blueprint(v1_bp)


def _register_error_handlers(app):
    """Register global error handlers.

    Delegates to app.errors module once it is implemented (task 1.4).
    """
    try:
        from app.errors import register_error_handlers

        register_error_handlers(app)
    except (ImportError, AttributeError):
        # Error handlers not yet implemented; use minimal defaults
        @app.errorhandler(404)
        def not_found(e):
            return {
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "details": None,
                },
            }, 404

        @app.errorhandler(500)
        def server_error(e):
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": None,
                },
            }, 500


def _register_security_headers(app):
    """Register after-request hook that adds security headers to all responses.

    Adds standard security headers to prevent common web attacks:
    - X-Content-Type-Options: Prevents MIME-type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS filtering
    - Strict-Transport-Security: Enforces HTTPS in production
    - Cache-Control: Prevents caching of sensitive responses
    """

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS only in production (when not debugging)
        if not app.config.get("DEBUG", False):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
