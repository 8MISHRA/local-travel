"""Shared test fixtures for the travel platform."""

import os

import pytest

os.environ["FLASK_ENV"] = "testing"


@pytest.fixture
def app():
    """Create a Flask application configured for testing."""
    from app import create_app

    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()
