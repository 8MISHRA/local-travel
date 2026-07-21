"""Application configuration classes.

All secrets are loaded from environment variables (Requirement 26.4).
All API endpoints are prefixed with /api/v1/ (Requirement 27.1).
"""

import os
from datetime import timedelta


class Config:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    # JWT
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
    JWT_ACCESS_EXPIRY = timedelta(minutes=15)
    JWT_REFRESH_EXPIRY = timedelta(days=7)
    JWT_ALGORITHM = "HS256"

    # Database — fix Render's postgres:// to postgresql://
    _database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/travel_platform"
    )
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
    )

    # CORS
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(
        ","
    )

    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200/hour")
    RATELIMIT_LOGIN = os.environ.get("RATELIMIT_LOGIN", "5/minute")
    RATELIMIT_REGISTER = os.environ.get("RATELIMIT_REGISTER", "3/minute")

    # Upload limits
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    # API
    API_PREFIX = "/api/v1"

    # Application
    APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/travel_platform_dev",
    )


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/travel_platform_test",
    )
    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False
    # Faster token expiry for tests
    JWT_ACCESS_EXPIRY = timedelta(minutes=5)
    JWT_REFRESH_EXPIRY = timedelta(hours=1)


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False

    # In production, these MUST be set via environment variables
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET = os.environ.get("JWT_SECRET")

    # Inherit SQLALCHEMY_DATABASE_URI from Config (which handles postgres:// fix)


# Configuration mapping by environment name
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
