import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from app.core.config import settings
from app.initial_data import create_superuser
from app.tasks.market_data import collect_market_data_job
from app.tasks.sentiment import collect_sentiment_job

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def startup() -> None:
    """Startup tasks - create superuser and initialize scheduler"""
    await create_superuser()
    
    # Validate required configuration for market data collection
    if not settings.ALPHA_VANTAGE_API_KEY:
        logger.warning(
            "ALPHA_VANTAGE_API_KEY not configured. Market data collection job will fail at runtime. "
            "Set ALPHA_VANTAGE_API_KEY environment variable to enable market data collection."
        )
    else:
        logger.info("ALPHA_VANTAGE_API_KEY configured - market data collection enabled")
    
    # Initialize APScheduler
    global scheduler
    scheduler = AsyncIOScheduler(
        jobstores={"default": MemoryJobStore()},
        timezone="UTC",
    )
    
    # Add hourly market data collection job
    # Runs every hour at minute 0 (e.g., 1:00, 2:00, 3:00, etc.)
    scheduler.add_job(
        collect_market_data_job,
        "cron",
        hour="*",
        minute=0,
        id="market_data_collection",
        name="Market Data Collection",
        max_instances=1,  # Prevent overlapping runs
        coalesce=True,  # Combine multiple pending executions into one
    )

    # Add hourly sentiment collection job (top of the hour + 5 minutes to stagger)
    scheduler.add_job(
        collect_sentiment_job,
        "cron",
        hour="*",
        minute=5,
        id="sentiment_collection",
        name="Sentiment Collection (Web Scraping)",
        max_instances=1,
        coalesce=True,
    )
    
    scheduler.start()
    logger.info("APScheduler started - market data and sentiment jobs scheduled")


async def shutdown() -> None:
    """Shutdown tasks - stop scheduler"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler stopped")
