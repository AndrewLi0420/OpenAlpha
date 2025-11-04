import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from app.core.config import settings
from app.initial_data import create_superuser
from app.services.ml_service import initialize_models
from app.tasks.market_data import collect_market_data_job
from app.tasks.sentiment import collect_sentiment_job
from app.tasks.recommendations import recommendations_job

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

    # Add hourly recommendations generation job (top of the hour + 10 minutes to follow data jobs)
    scheduler.add_job(
        recommendations_job,
        "cron",
        hour="*",
        minute=10,
        id="recommendations_generation",
        name="Recommendations Generation",
        max_instances=1,
        coalesce=True,
    )
    
    scheduler.start()
    logger.info("APScheduler started - market data, sentiment, and recommendations jobs scheduled")
    
    # Initialize ML models for inference
    logger.info("Initializing ML models for inference...")
    try:
        model_init_results = initialize_models()
        nn_status = model_init_results["neural_network"]
        rf_status = model_init_results["random_forest"]
        
        if nn_status["loaded"]:
            logger.info("Neural network model loaded: version %s", nn_status["version"])
        else:
            logger.warning("Neural network model not loaded: %s", nn_status.get("error", "Unknown error"))
        
        if rf_status["loaded"]:
            logger.info("Random Forest model loaded: version %s", rf_status["version"])
        else:
            logger.warning("Random Forest model not loaded: %s", rf_status.get("error", "Unknown error"))
        
        if nn_status["loaded"] or rf_status["loaded"]:
            logger.info("ML inference service ready (at least one model loaded)")
        else:
            logger.error("ML inference service unavailable: No models loaded")
    except Exception as e:
        logger.error("Failed to initialize ML models: %s", e, exc_info=True)


async def shutdown() -> None:
    """Shutdown tasks - stop scheduler"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler stopped")
