"""Market data collection service for financial APIs"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Rate limiting configuration for Alpha Vantage free tier
ALPHA_VANTAGE_RATE_LIMIT_CALLS_PER_MINUTE = 5
ALPHA_VANTAGE_RATE_LIMIT_DELAY_SECONDS = 12  # 60 seconds / 5 calls = 12 seconds between calls

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.min_delay = 60.0 / calls_per_minute
        self.last_call_time = 0.0
    
    async def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limits"""
        current_time = asyncio.get_event_loop().time()
        time_since_last_call = current_time - self.last_call_time
        
        if time_since_last_call < self.min_delay:
            wait_time = self.min_delay - time_since_last_call
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        self.last_call_time = asyncio.get_event_loop().time()


# Global rate limiter instance
_rate_limiter = RateLimiter(ALPHA_VANTAGE_RATE_LIMIT_CALLS_PER_MINUTE)


async def collect_market_data_from_alpha_vantage(
    stock_symbol: str,
) -> dict[str, Any] | None:
    """
    Collect market data from Alpha Vantage API for a single stock.
    
    Args:
        stock_symbol: Stock symbol (e.g., 'AAPL')
    
    Returns:
        dict with keys: price (float), volume (int), timestamp (datetime UTC)
        Returns None on failure after all retries
    
    Raises:
        ValueError: If API key is not configured
    """
    if not settings.ALPHA_VANTAGE_API_KEY:
        raise ValueError("ALPHA_VANTAGE_API_KEY not configured in settings")
    
    # Respect rate limits
    await _rate_limiter.wait_if_needed()
    
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": stock_symbol,
        "apikey": settings.ALPHA_VANTAGE_API_KEY,
    }
    
    # Retry logic with exponential backoff
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors in response
                if "Error Message" in data:
                    error_msg = data["Error Message"]
                    logger.error(
                        f"Alpha Vantage API error for {stock_symbol}: {error_msg}"
                    )
                    # Don't retry on API errors (invalid symbol, etc.)
                    return None
                
                if "Note" in data:
                    # Rate limit message
                    note = data["Note"]
                    logger.warning(
                        f"Alpha Vantage rate limit for {stock_symbol}: {note}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        # Wait longer for rate limit (60 seconds)
                        await asyncio.sleep(60)
                        continue
                    return None
                
                # Parse successful response
                if "Global Quote" not in data:
                    logger.warning(
                        f"Unexpected response format for {stock_symbol}: {data}"
                    )
                    return None
                
                quote = data["Global Quote"]
                
                # Extract price and volume
                try:
                    price_str = quote.get("05. price", "")
                    volume_str = quote.get("06. volume", "")
                    
                    if not price_str or not volume_str:
                        logger.warning(
                            f"Missing price or volume in response for {stock_symbol}"
                        )
                        return None
                    
                    price = float(price_str)
                    volume = int(volume_str)
                    
                    # Validate numeric values
                    if price <= 0 or volume < 0:
                        logger.warning(
                            f"Invalid price or volume for {stock_symbol}: "
                            f"price={price}, volume={volume}"
                        )
                        return None
                    
                    # Extract timestamp from quote (use latest trading day)
                    # Alpha Vantage doesn't provide exact timestamp, so we use current UTC
                    timestamp = datetime.now(timezone.utc)
                    
                    logger.debug(
                        f"Successfully collected data for {stock_symbol}: "
                        f"price={price}, volume={volume}"
                    )
                    
                    return {
                        "price": price,
                        "volume": volume,
                        "timestamp": timestamp,
                    }
                    
                except (ValueError, KeyError) as e:
                    logger.error(
                        f"Error parsing response for {stock_symbol}: {e}. "
                        f"Response: {quote}"
                    )
                    return None
                    
        except httpx.HTTPStatusError as e:
            last_error = e
            status_code = e.response.status_code
            
            if status_code == 429:  # Rate limit exceeded
                logger.warning(
                    f"Rate limit exceeded for {stock_symbol} (attempt {attempt + 1})"
                )
                if attempt < MAX_RETRIES - 1:
                    # Wait 60 seconds for rate limit reset
                    await asyncio.sleep(60)
                    continue
            
            elif status_code >= 500:  # Server errors - retry
                logger.warning(
                    f"Server error {status_code} for {stock_symbol} "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})"
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                    continue
            
            else:  # Client errors (4xx) - don't retry
                logger.error(
                    f"HTTP {status_code} error for {stock_symbol}: {e.response.text}"
                )
                return None
                
        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(
                f"Timeout for {stock_symbol} (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])
                continue
                
        except Exception as e:
            last_error = e
            logger.error(
                f"Unexpected error collecting data for {stock_symbol} "
                f"(attempt {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])
                continue
    
    # All retries exhausted
    logger.error(
        f"Failed to collect market data for {stock_symbol} after {MAX_RETRIES} "
        f"attempts. Last error: {last_error}"
    )
    return None


async def collect_market_data(
    stock_symbol: str,
    session: AsyncSession | None = None,
) -> dict[str, Any] | None:
    """
    Collect market data for a stock symbol.
    
    This is the main entry point for market data collection.
    Currently uses Alpha Vantage API.
    
    Args:
        stock_symbol: Stock symbol (e.g., 'AAPL')
        session: Optional database session (not used currently but kept for interface compatibility)
    
    Returns:
        dict with keys: price (float), volume (int), timestamp (datetime UTC)
        Returns None on failure
    """
    return await collect_market_data_from_alpha_vantage(stock_symbol)

