"""Integration tests for market data collection service and scheduled task"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

# Import models to ensure relationships are registered
from app.models import Stock, MarketData  # noqa: F401
from app.users.models import User  # noqa: F401
from app.models.user_preferences import UserPreferences  # noqa: F401

from app.crud.stocks import create_stock, get_all_stocks
from app.crud.market_data import get_latest_market_data, get_market_data_count
from app.services.data_collection import collect_market_data
from app.tasks.market_data import collect_market_data_job, collect_market_data_for_stocks


@pytest.mark.asyncio
async def test_collect_market_data_success(db_session):
    """Test successful market data collection (AC: 1, 3)"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Mock successful API response
    mock_response_data = {
        "Global Quote": {
            "05. price": "150.50",
            "06. volume": "1000000",
        }
    }
    
    with patch("app.services.data_collection.settings.ALPHA_VANTAGE_API_KEY", "test-api-key"):
        with patch("app.services.data_collection.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            # Mock rate limiter to skip delays in tests
            with patch("app.services.data_collection._rate_limiter.wait_if_needed"):
                data = await collect_market_data(stock.symbol, db_session)
    
            assert data is not None
            assert data["price"] == 150.50
            assert data["volume"] == 1000000
            assert isinstance(data["timestamp"], datetime)


@pytest.mark.asyncio
async def test_collect_market_data_api_error(db_session):
    """Test API error handling (AC: 5)"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="INVALID",
        company_name="Invalid Stock",
    )
    
    # Mock API error response
    mock_response_data = {
        "Error Message": "Invalid API call. Please retry or visit the documentation."
    }
    
    with patch("app.services.data_collection.settings.ALPHA_VANTAGE_API_KEY", "test-api-key"):
        with patch("app.services.data_collection.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            # Mock rate limiter
            with patch("app.services.data_collection._rate_limiter.wait_if_needed"):
                data = await collect_market_data(stock.symbol, db_session)
        
            assert data is None  # Should return None on API error


@pytest.mark.asyncio
async def test_collect_market_data_rate_limit_exceeded(db_session):
    """Test rate limit exceeded handling (AC: 6)"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Mock rate limit response
    mock_response_data = {
        "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute..."
    }
    
    with patch("app.services.data_collection.settings.ALPHA_VANTAGE_API_KEY", "test-api-key"):
        with patch("app.services.data_collection.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_client_instance
            
            # Mock rate limiter and sleep
            with patch("app.services.data_collection._rate_limiter.wait_if_needed"):
                with patch("app.services.data_collection.asyncio.sleep") as mock_sleep:
                    data = await collect_market_data(stock.symbol, db_session)
                    
                    # Should have waited 60 seconds for rate limit (after rate limit detected)
                    # Rate limit note triggers 60s wait, so expect at least 2 calls (initial attempt + retry after 60s)
                    assert mock_sleep.call_count >= 2  # At least 2 retry attempts with 60s delays
        
        assert data is None  # Should return None after exhausting retries


@pytest.mark.asyncio
async def test_collect_market_data_retry_logic(db_session):
    """Test exponential backoff retry logic (AC: 5)"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Mock server error (500) that should trigger retries
    from httpx import HTTPStatusError
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    http_error = HTTPStatusError("Server Error", request=MagicMock(), response=mock_response)
    
    with patch("app.services.data_collection.settings.ALPHA_VANTAGE_API_KEY", "test-api-key"):
        with patch("app.services.data_collection.httpx.AsyncClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get = AsyncMock(side_effect=http_error)
            mock_client.return_value = mock_client_instance
            
            # Mock rate limiter and sleep
            with patch("app.services.data_collection._rate_limiter.wait_if_needed"):
                with patch("app.services.data_collection.asyncio.sleep") as mock_sleep:
                    data = await collect_market_data(stock.symbol, db_session)
                    
                    # Should have retried 3 times with exponential backoff (1s, 2s, 4s)
                    # With 3 attempts total, we sleep 2 times (before retry 1 and retry 2)
                    assert mock_sleep.call_count == 2  # 2 sleeps for 3 attempts (attempt 0, 1, 2)
                    # Verify exponential backoff delays
                    from unittest.mock import call
                    call_args = [c[0][0] for c in mock_sleep.call_args_list]
                    assert 1.0 in call_args or 2.0 in call_args  # First or second retry delay
        
        assert data is None  # Should fail after retries


@pytest.mark.asyncio
async def test_collect_market_data_batch_processing(db_session):
    """Test batch processing with graceful degradation (AC: 1, 5)"""
    # Create multiple stocks
    stocks = []
    for i in range(10):
        stock = await create_stock(
            session=db_session,
            symbol=f"STOCK{i}",
            company_name=f"Stock {i} Inc.",
        )
        stocks.append(stock)
    
    with patch("app.services.data_collection.settings.ALPHA_VANTAGE_API_KEY", "test-api-key"):
        with patch("app.services.data_collection.collect_market_data_from_alpha_vantage") as mock_collect:
            # Set up mock to return success for some, None for others
            async def mock_collect_func(symbol, session=None):
                if "STOCK0" in symbol or "STOCK1" in symbol:
                    return None  # Simulate failure
                return {
                    "price": 100.00,
                    "volume": 1000000,
                    "timestamp": datetime.now(timezone.utc),
                }
            
            mock_collect.side_effect = mock_collect_func
            
            # Process in batches
            stats = await collect_market_data_for_stocks(
                session=db_session,
                stocks=stocks,
                batch_size=5,  # 2 batches of 5
            )
            
            # Should have processed successfully despite some failures
            assert stats["total"] == 10
            assert stats["successful"] == 8  # 10 - 2 failures
            assert stats["failed"] == 2  # 2 failures
            assert stats["successful"] + stats["failed"] == stats["total"]


@pytest.mark.asyncio
async def test_collect_market_data_job_execution(db_session):
    """Test APScheduler job execution (AC: 2)"""
    # Create test stocks
    stocks = []
    for i in range(5):
        stock = await create_stock(
            session=db_session,
            symbol=f"TEST{i}",
            company_name=f"Test Stock {i}",
        )
        stocks.append(stock)
    
    # Mock the collection function to return success
    async def mock_collect(symbol, session=None):
        return {
            "price": 100.00,
            "volume": 1000000,
            "timestamp": datetime.now(timezone.utc),
        }
    
    # Mock the database engine creation and session
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from unittest.mock import MagicMock, AsyncMock
    
    mock_engine = AsyncMock()
    mock_engine.dispose = AsyncMock()  # Make dispose async
    
    # Create a context manager that returns db_session
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=db_session)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    mock_sessionmaker = MagicMock(return_value=mock_session_context)
    
    with patch("app.services.data_collection.settings.ALPHA_VANTAGE_API_KEY", "test-api-key"):
        # Patch the internal function directly since it's used by collect_market_data
        with patch("app.services.data_collection.collect_market_data_from_alpha_vantage", side_effect=mock_collect):
            with patch("app.tasks.market_data.create_async_engine", return_value=mock_engine):
                with patch("app.tasks.market_data.sessionmaker", return_value=mock_sessionmaker):
                    # Execute job
                    await collect_market_data_job()
                    
                    # Verify data was collected
                    count = await get_market_data_count(db_session)
                    assert count == 5  # Should have collected data for all 5 stocks


@pytest.mark.asyncio
async def test_market_data_storage_with_timestamps(db_session):
    """Test that market data is stored with proper timestamps (AC: 4)"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Mock successful collection
    timestamp = datetime.now(timezone.utc)
    mock_data = {
        "price": 150.50,
        "volume": 1000000,
        "timestamp": timestamp,
    }
    
    with patch("app.services.data_collection.settings.ALPHA_VANTAGE_API_KEY", "test-api-key"):
        with patch("app.services.data_collection.collect_market_data_from_alpha_vantage", return_value=mock_data):
            from app.services.data_collection import collect_market_data
            from app.crud.market_data import create_market_data
            
            data = await collect_market_data(stock.symbol, db_session)
            assert data is not None
            
            # Store in database
            market_data = await create_market_data(
                session=db_session,
                stock_id=stock.id,
                price=data["price"],
                volume=data["volume"],
                timestamp=data["timestamp"],
            )
            
            # Verify storage
            assert market_data.stock_id == stock.id
            assert float(market_data.price) == 150.50
            assert market_data.volume == 1000000
            # Timestamp comparison (database may store naive datetime)
            stored_ts = market_data.timestamp.replace(tzinfo=timezone.utc) if market_data.timestamp.tzinfo is None else market_data.timestamp
            expected_ts = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
            assert abs((stored_ts - expected_ts).total_seconds()) < 1
            
            # Verify can retrieve
            latest = await get_latest_market_data(db_session, stock.id)
            assert latest is not None
