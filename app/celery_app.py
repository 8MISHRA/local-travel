"""Celery application configuration.

Creates a Celery instance that operates within the Flask application context,
allowing background tasks to access Flask extensions (db, config, etc.).
"""

from celery import Celery


def make_celery(app=None):
    """Create a Celery instance configured from the Flask app.

    Args:
        app: Flask application instance. If None, creates one via the factory.

    Returns:
        Configured Celery instance with Flask app context.
    """
    if app is None:
        from app import create_app

        app = create_app()

    celery = Celery(
        app.import_name,
        broker=app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        backend=app.config.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    )

    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )

    class ContextTask(celery.Task):
        """Celery task that runs within the Flask application context."""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery
