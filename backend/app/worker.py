from saq import Queue
from pydantic.v1.utils import import_string

from .core.config import settings

# Note: Background job queue uses SAQ which may have its own database connections
# For now, worker tasks can use SQLAlchemy sessions via dependency injection
# If SAQ requires separate database connections, we'll configure them here

BACKGROUND_FUNCTIONS = [
    "app.users.tasks.log_user_email",
    "app.services.email.send_email_task",
]
FUNCTIONS = [import_string(bg_func) for bg_func in BACKGROUND_FUNCTIONS]


async def startup(_: dict):
    """
    Background worker startup.
    Note: Database connections for background tasks should use SQLAlchemy sessions
    via dependency injection rather than direct connections.
    """
    # TODO: If SAQ needs direct database access, configure SQLAlchemy connection here
    pass


async def shutdown(_: dict):
    """
    Background worker shutdown.
    """
    # TODO: Clean up any database connections if configured above
    pass


queue = Queue.from_url(str(settings.REDIS_URL))

settings = {
    "queue": queue,
    "functions": FUNCTIONS,
    "concurrency": 10,
    "startup": startup,
    "shutdown": shutdown,
}
