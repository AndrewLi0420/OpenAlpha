from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from app.core.config import settings
from app.core.logger import logger
from app.initial_data import create_superuser
from app.services.ml_service import initialize_models
from app.tasks.market_data import collect_market_data_job
from app.tasks.sentiment import collect_sentiment_job
from app.tasks.recommendations import recommendations_job

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def startup() -> None:
    """Startup tasks - create superuser and initialize scheduler"""
    try:
        await create_superuser()
        logger.info("Superuser check completed")
    except Exception as e:
        logger.error("Error creating superuser: %s", e, exc_info=True)
    
    # Market data collection uses yfinance (no API key required)
    logger.info("Market data collection enabled (using yfinance)")
    
    # Initialize APScheduler
    try:
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
    except Exception as e:
        logger.error("Error initializing scheduler: %s", e, exc_info=True)
    
    # Initialize ML models for inference
    # Run in executor since initialize_models() is a blocking sync function
    import asyncio
    import os
    from concurrent.futures import ThreadPoolExecutor
    
    # Diagnostic logging: Check working directory and ml-models folder
    logger.info("=== ML Model Initialization Diagnostics ===")
    logger.info("Working directory: %s", os.getcwd())
    
    # Check for ml-models folder from current working directory
    if os.path.exists("ml-models"):
        logger.info("ml-models folder found from current path, contents: %s", os.listdir("ml-models"))
    else:
        logger.warning("ml-models folder NOT found from current path!")
    
    # Also check relative to backend directory (common when running from backend/)
    backend_ml_models = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml-models")
    if os.path.exists(backend_ml_models):
        logger.info("ml-models folder found relative to backend: %s", backend_ml_models)
        logger.info("Contents: %s", os.listdir(backend_ml_models))
    else:
        logger.warning("ml-models folder NOT found relative to backend: %s", backend_ml_models)
    
    # Check backend root (1 level up from app/lifetime.py, which is where models actually are)
    # lifetime.py is at backend/app/lifetime.py, so going up 1 level gives backend/
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_ml_models = os.path.join(backend_root, "ml-models")
    logger.info("Backend root (calculated from lifetime.py path): %s", backend_root)
    if os.path.exists(backend_ml_models):
        logger.info("ml-models folder found at backend root: %s", backend_ml_models)
        logger.info("Contents: %s", os.listdir(backend_ml_models))
    else:
        logger.warning("ml-models folder NOT found at backend root: %s", backend_ml_models)
    
    logger.info("Initializing ML models for inference...")
    try:
        # Run blocking model loading in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            model_init_results = await loop.run_in_executor(executor, initialize_models)
        
        # Log the exact return structure from initialize_models()
        logger.info("=== initialize_models() return structure ===")
        logger.info("Full results dict: %s", model_init_results)
        
        nn_status = model_init_results["neural_network"]
        rf_status = model_init_results["random_forest"]
        
        logger.info("Neural network status: loaded=%s, version=%s, error=%s", 
                   nn_status["loaded"], nn_status["version"], nn_status.get("error"))
        logger.info("Random Forest status: loaded=%s, version=%s, error=%s", 
                   rf_status["loaded"], rf_status["version"], rf_status.get("error"))
        
        if nn_status["loaded"]:
            logger.info("✓ Neural network model loaded: version %s", nn_status["version"])
        else:
            logger.warning("✗ Neural network model not loaded: %s", nn_status.get("error", "Unknown error"))
        
        if rf_status["loaded"]:
            logger.info("✓ Random Forest model loaded: version %s", rf_status["version"])
        else:
            logger.warning("✗ Random Forest model not loaded: %s", rf_status.get("error", "Unknown error"))
        
        if nn_status["loaded"] or rf_status["loaded"]:
            logger.info("✓ ML inference service ready (at least one model loaded)")
        else:
            logger.error("✗ ML inference service unavailable: No models loaded")
            logger.error("   Please check that model files exist in ml-models/ directory")
            logger.error("   Run: python scripts/train_models.py to train models if needed")
    except Exception as e:
        logger.error("Failed to initialize ML models: %s", e, exc_info=True)
        import traceback
        logger.error("Traceback: %s", traceback.format_exc())


async def shutdown() -> None:
    """Shutdown tasks - stop scheduler"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler stopped")
