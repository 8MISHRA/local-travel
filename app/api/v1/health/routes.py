"""Health check endpoint for deployment verification.

Validates: Requirements 24.1, 24.2, 24.3
- 24.1: GET /health returns service status, database connectivity, app version
- 24.2: No authentication required
- 24.3: Returns HTTP 503 if database is unreachable
"""

from flask import Blueprint, current_app
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("", methods=["GET"])
def health_check():
    """Health check endpoint.

    Returns HTTP 200 with status=healthy when all systems are operational.
    Returns HTTP 503 with status=unhealthy when database is unreachable.

    No authentication required.
    """
    db_status = "connected"
    status = "healthy"
    http_code = 200

    # Check database connectivity
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        status = "unhealthy"
        http_code = 503

    version = current_app.config.get("APP_VERSION", "1.0.0")

    from flask import jsonify

    return jsonify({
        "status": status,
        "database": db_status,
        "version": version,
    }), http_code
