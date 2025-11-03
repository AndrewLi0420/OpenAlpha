"""Scheduled task for market data collection"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.crud.stocks import get_all_stocks
from app.crud.market_data import create_market_data
from app.services.data_collection import collect_market_data

logger = logging.getLogger(__name__)

# Batch processing configuration
BATCH_SIZE = 50  # Process 50 stocks per batch to manage API rate limits


async def collect_market_data_for_stocks(
    session: AsyncSession,
    stocks: list,
    batch_size: int = BATCH_SIZE,
) -> dict[str, int]:
    """
    Collect market data for a list of stocks in batches.
    
    Implements graceful degradation: continues processing even if some stocks fail.
    
    Args:
        session: Database session
        stocks: List of Stock instances
        batch_size: Number of stocks to process per batch
    
    Returns:
        dict with statistics:
        - total: Total stocks to process
        - successful: Number of stocks successfully collected
        - failed: Number of stocks that failed
    """
    stats = {
        "total": len(stocks),
        "successful": 0,
        "failed": 0,
    }
    
    # Process stocks in batches
    for batch_start in range(0, len(stocks), batch_size):
        batch_end = min(batch_start + batch_size, len(stocks))
        batch = stocks[batch_start:batch_end]
        batch_num = (batch_start // batch_size) + 1
        total_batches = (len(stocks) + batch_size - 1) // batch_size
        
        logger.info(
            f"Processing batch {batch_num}/{total_batches}: "
            f"stocks {batch_start + 1}-{batch_end} of {len(stocks)}"
        )
        
        # Process batch: collect data concurrently, then store sequentially
        # Note: Data collection happens concurrently (with rate limiting in service),
        # but database commits are sequential to avoid session conflicts
        async def collect_for_stock(stock):
            """Collect data for a single stock"""
            try:
                data = await collect_market_data(stock.symbol, session)
                return (stock, data) if data else (stock, None)
            except Exception as e:
                logger.error(f"Error collecting data for {stock.symbol}: {e}")
                return (stock, None)
        
        # Collect data concurrently (rate limiting handled in service)
        collection_tasks = [collect_for_stock(stock) for stock in batch]
        collection_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # Process results and store in database sequentially
        for result in collection_results:
            if isinstance(result, Exception):
                stats["failed"] += 1
                continue
            
            stock, data = result
            if data is None:
                stats["failed"] += 1
                continue
            
            # Store in database sequentially to avoid session conflicts
            try:
                await create_market_data(
                    session=session,
                    stock_id=stock.id,
                    price=data["price"],
                    volume=data["volume"],
                    timestamp=data["timestamp"],
                )
                stats["successful"] += 1
                logger.debug(
                    f"Successfully collected and stored market data for {stock.symbol}: "
                    f"price={data['price']}, volume={data['volume']}"
                )
            except Exception as e:
                logger.error(
                    f"Exception storing data for {stock.symbol}: {e}",
                    exc_info=True,
                )
                stats["failed"] += 1
        
        logger.info(
            f"Batch {batch_num} completed: "
            f"{stats['successful']} successful, {stats['failed']} failed so far"
        )
        
        # Add delay between batches to respect rate limits
        # The service already handles per-call rate limiting, but we add batch delay too
        if batch_end < len(stocks):
            await asyncio.sleep(1)  # 1 second between batches
    
    return stats


async def _process_single_stock(
    session: AsyncSession,
    stock,
) -> bool:
    """
    Process a single stock: collect data and store in database.
    
    Args:
        session: Database session
        stock: Stock instance
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Collect market data from API
        data = await collect_market_data(stock.symbol, session)
        
        if data is None:
            logger.warning(
                f"Failed to collect market data for {stock.symbol}"
            )
            return False
        
        # Store in database
        await create_market_data(
            session=session,
            stock_id=stock.id,
            price=data["price"],
            volume=data["volume"],
            timestamp=data["timestamp"],
        )
        
        logger.debug(
            f"Successfully collected and stored market data for {stock.symbol}: "
            f"price={data['price']}, volume={data['volume']}"
        )
        
        return True
        
    except Exception as e:
        logger.error(
            f"Exception processing stock {stock.symbol}: {e}",
            exc_info=True,
        )
        return False


async def collect_market_data_job() -> None:
    """
    APScheduler job function for hourly market data collection.
    
    This function:
    1. Gets all Fortune 500 stocks
    2. Processes them in batches of 50
    3. Collects market data with rate limiting
    4. Stores results in database
    5. Reports aggregate statistics
    
    Handles graceful degradation: continues processing even if some stocks fail.
    """
    logger.info("Starting market data collection job")
    start_time = datetime.now(timezone.utc)
    
    # Create database session for this job
    # Note: Creating separate engine here rather than reusing app engine is intentional:
    # - This job runs in background context, independent of web request lifecycle
    # - Separate engine provides isolation and proper connection pool management
    # - Engine is disposed after job completes, preventing resource leaks
    # Alternative: Could reuse engine from app.db.config, but current approach is safer
    engine = None
    try:
        engine = create_async_engine(str(settings.DATABASE_URI))
        async_session_maker = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session_maker() as session:
            # Get all stocks
            stocks = await get_all_stocks(session)
            
            if not stocks:
                logger.warning("No stocks found in database. Skipping market data collection.")
                return
            
            logger.info(f"Found {len(stocks)} stocks to process")
            
            # Process stocks in batches with graceful degradation
            stats = await collect_market_data_for_stocks(
                session=session,
                stocks=stocks,
                batch_size=BATCH_SIZE,
            )
            
            # Log aggregate results
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Market data collection job completed: "
                f"Processed {stats['successful']}/{stats['total']} stocks successfully "
                f"({stats['failed']} failed) in {duration:.1f} seconds"
            )
            
            if stats["failed"] > 0:
                logger.warning(
                    f"{stats['failed']} stocks failed to collect data. "
                    f"They will be retried on the next cycle."
                )
            
            # Track data freshness (AC 7)
            from app.crud.market_data import get_stocks_with_stale_data
            
            stale_stocks = await get_stocks_with_stale_data(session, max_age_hours=1)
            if stale_stocks:
                logger.info(
                    f"Data freshness check: {len(stale_stocks)} stocks have stale data "
                    f"(older than 1 hour or no data)"
                )
        
        # Cleanup: dispose engine to release connections
        if engine:
            await engine.dispose()
    
    except Exception as e:
        logger.error(
            f"Fatal error in market data collection job: {e}",
            exc_info=True,
        )
        # Ensure engine is disposed even on error
        if engine:
            try:
                await engine.dispose()
            except Exception:
                pass
        raise


# For testing and manual execution
async def run_market_data_collection() -> None:
    """
    Run market data collection manually (for testing or manual triggers).
    
    This is a convenience function that can be called directly.
    """
    await collect_market_data_job()

