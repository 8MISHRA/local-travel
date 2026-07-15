"""Flask extension instances.

Extensions are instantiated here without an app reference and later
initialized with the app inside the create_app() factory function.

Validates: Requirement 27.1 - All endpoints prefixed with /api/v1/
(extensions support the app factory that enforces this structure).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
