"""Tests for the Flask app factory and extensions setup."""

import os


class TestCreateApp:
    """Test the create_app factory function."""

    def test_creates_flask_app(self, app):
        """App factory returns a Flask instance."""
        from flask import Flask

        assert isinstance(app, Flask)

    def test_uses_testing_config(self, app):
        """App loads the testing configuration when specified."""
        assert app.config["TESTING"] is True
        assert app.config["DEBUG"] is True

    def test_default_config_is_development(self):
        """App defaults to development config when FLASK_ENV is not set."""
        from app import create_app

        os.environ.pop("FLASK_ENV", None)
        app = create_app()
        assert app.config["DEBUG"] is True
        assert app.config.get("TESTING") is not True

    def test_api_prefix_configured(self, app):
        """Config includes /api/v1 prefix."""
        assert app.config["API_PREFIX"] == "/api/v1"

    def test_v1_blueprint_registered(self, app):
        """The v1 blueprint is registered on the app."""
        assert "v1" in app.blueprints

    def test_cors_headers_present(self, client):
        """CORS headers are set on responses for allowed origins."""
        resp = client.options(
            "/api/v1/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "Access-Control-Allow-Origin" in resp.headers

    def test_cors_allows_authorization_header(self, client):
        """CORS allows Authorization and Content-Type headers (Requirement 26.3)."""
        resp = client.options(
            "/api/v1/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,Content-Type",
            },
        )
        allowed = resp.headers.get("Access-Control-Allow-Headers", "")
        assert "Authorization" in allowed or "authorization" in allowed.lower()
        assert "Content-Type" in allowed or "content-type" in allowed.lower()

    def test_cors_supports_credentials(self, client):
        """CORS allows credentials for cookie-based auth (Requirement 26.5)."""
        resp = client.options(
            "/api/v1/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_security_headers_present(self, client):
        """Security headers are set on all responses."""
        resp = client.get("/api/v1/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_max_content_length_configured(self, app):
        """MAX_CONTENT_LENGTH is set to 10MB (Requirement 26.3)."""
        assert app.config["MAX_CONTENT_LENGTH"] == 10 * 1024 * 1024

    def test_session_cookie_httponly(self, app):
        """Session cookies are configured with httpOnly flag (Requirement 26.5)."""
        assert app.config["SESSION_COOKIE_HTTPONLY"] is True

    def test_session_cookie_samesite(self, app):
        """Session cookies are configured with SameSite=Lax."""
        assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"

    def test_404_error_handler_json(self, client):
        """404 errors return structured JSON response."""
        resp = client.get("/nonexistent-path")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


class TestExtensions:
    """Test that extensions are properly initialized."""

    def test_db_initialized(self, app):
        """SQLAlchemy is bound to the app."""
        from app.extensions import db

        with app.app_context():
            assert db.engine is not None

    def test_marshmallow_initialized(self, app):
        """Marshmallow is initialized with the app."""
        from app.extensions import ma

        assert ma is not None

    def test_migrate_initialized(self, app):
        """Flask-Migrate is initialized."""
        from app.extensions import migrate

        assert migrate is not None

    def test_limiter_initialized(self, app):
        """Flask-Limiter is initialized (disabled in testing)."""
        from app.extensions import limiter

        assert limiter is not None
        assert limiter.enabled is False


class TestCeleryApp:
    """Test Celery application configuration."""

    def test_make_celery_creates_instance(self, app):
        """make_celery returns a Celery instance."""
        from app.celery_app import make_celery

        celery = make_celery(app)
        assert celery is not None
        assert celery.main == "app"

    def test_celery_broker_from_config(self, app):
        """Celery uses broker URL from Flask config."""
        from app.celery_app import make_celery

        celery = make_celery(app)
        assert celery.conf.broker_url == app.config["CELERY_BROKER_URL"]

    def test_celery_backend_from_config(self, app):
        """Celery uses result backend from Flask config."""
        from app.celery_app import make_celery

        celery = make_celery(app)
        assert celery.conf.result_backend == app.config["CELERY_RESULT_BACKEND"]

    def test_celery_task_runs_in_app_context(self, app):
        """Celery tasks execute within Flask app context."""
        from app.celery_app import make_celery

        celery = make_celery(app)

        @celery.task
        def dummy_task():
            from flask import current_app

            return current_app.config["TESTING"]

        # Invoke synchronously
        with app.app_context():
            result = dummy_task()
            assert result is True
