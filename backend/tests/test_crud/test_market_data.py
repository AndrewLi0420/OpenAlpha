"""Tests for market data CRUD operations"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Import models to ensure relationships are registered
# Import all models to ensure relationships resolve correctly
from app.models import Stock, MarketData  # noqa: F401
# Import User-related models to satisfy relationships
from app.users.models import User  # noqa: F401
from app.models.user_preferences import UserPreferences  # noqa: F401
from app.crud.stocks import create_stock
from app.crud.market_data import (
    create_market_data,
    get_latest_market_data,
    get_market_data_history,
    get_market_data_count,
    get_stocks_with_stale_data,
)


@pytest.mark.asyncio
async def test_create_market_data(db_session):
    """Test creating a market data record"""
    # Create a stock first
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Create market data
    timestamp = datetime.now(timezone.utc)
    market_data = await create_market_data(
        session=db_session,
        stock_id=stock.id,
        price=150.50,
        volume=1000000,
        timestamp=timestamp,
    )
    
    assert market_data.stock_id == stock.id
    assert float(market_data.price) == 150.50
    assert market_data.volume == 1000000
    # Compare timestamps (database may store naive datetime, so convert for comparison)
    stored_timestamp = market_data.timestamp
    if stored_timestamp.tzinfo is None:
        stored_timestamp = stored_timestamp.replace(tzinfo=timezone.utc)
    assert abs((stored_timestamp - timestamp.replace(tzinfo=None).replace(tzinfo=timezone.utc)).total_seconds()) < 1
    assert market_data.id is not None


@pytest.mark.asyncio
async def test_get_latest_market_data(db_session):
    """Test getting latest market data for a stock"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Create multiple market data records with different timestamps
    now = datetime.now(timezone.utc)
    
    # Older data
    await create_market_data(
        session=db_session,
        stock_id=stock.id,
        price=140.00,
        volume=800000,
        timestamp=now - timedelta(hours=2),
    )
    
    # Latest data
    latest_timestamp = now - timedelta(hours=1)
    await create_market_data(
        session=db_session,
        stock_id=stock.id,
        price=150.50,
        volume=1000000,
        timestamp=latest_timestamp,
    )
    
    # Get latest
    latest = await get_latest_market_data(db_session, stock.id)
    
    assert latest is not None
    assert float(latest.price) == 150.50
    assert latest.volume == 1000000
    # Compare timestamps (database stores naive datetime, convert for comparison)
    stored_ts = latest.timestamp.replace(tzinfo=timezone.utc) if latest.timestamp.tzinfo is None else latest.timestamp
    expected_ts = latest_timestamp.replace(tzinfo=timezone.utc) if latest_timestamp.tzinfo is None else latest_timestamp
    assert abs((stored_ts - expected_ts).total_seconds()) < 1


@pytest.mark.asyncio
async def test_get_latest_market_data_no_data(db_session):
    """Test getting latest market data when none exists"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Try to get latest (should return None)
    latest = await get_latest_market_data(db_session, stock.id)
    assert latest is None


@pytest.mark.asyncio
async def test_get_market_data_history(db_session):
    """Test getting historical market data within date range"""
    # Create a stock
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Create market data records
    base_time = datetime.now(timezone.utc)
    
    # Out of range (too old)
    await create_market_data(
        session=db_session,
        stock_id=stock.id,
        price=130.00,
        volume=500000,
        timestamp=base_time - timedelta(days=2),
    )
    
    # In range
    await create_market_data(
        session=db_session,
        stock_id=stock.id,
        price=140.00,
        volume=700000,
        timestamp=base_time - timedelta(hours=12),
    )
    
    await create_market_data(
        session=db_session,
        stock_id=stock.id,
        price=150.00,
        volume=900000,
        timestamp=base_time - timedelta(hours=6),
    )
    
    # Out of range (too new)
    await create_market_data(
        session=db_session,
        stock_id=stock.id,
        price=160.00,
        volume=1100000,
        timestamp=base_time + timedelta(hours=1),
    )
    
    # Get history for last 24 hours
    start_date = base_time - timedelta(days=1)
    end_date = base_time
    
    history = await get_market_data_history(
        db_session, stock.id, start_date, end_date
    )
    
    assert len(history) == 2
    assert float(history[0].price) == 140.00  # Older first (ascending order)
    assert float(history[1].price) == 150.00


@pytest.mark.asyncio
async def test_get_market_data_count(db_session):
    """Test getting market data count"""
    # Create stocks
    stock1 = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    stock2 = await create_stock(
        session=db_session,
        symbol="MSFT",
        company_name="Microsoft Corporation",
    )
    
    # Create market data for stock1
    await create_market_data(
        session=db_session,
        stock_id=stock1.id,
        price=150.00,
        volume=1000000,
        timestamp=datetime.now(timezone.utc),
    )
    
    await create_market_data(
        session=db_session,
        stock_id=stock1.id,
        price=151.00,
        volume=1100000,
        timestamp=datetime.now(timezone.utc),
    )
    
    # Create market data for stock2
    await create_market_data(
        session=db_session,
        stock_id=stock2.id,
        price=300.00,
        volume=2000000,
        timestamp=datetime.now(timezone.utc),
    )
    
    # Test total count
    total_count = await get_market_data_count(db_session)
    assert total_count == 3
    
    # Test count for specific stock
    stock1_count = await get_market_data_count(db_session, stock_id=stock1.id)
    assert stock1_count == 2
    
    stock2_count = await get_market_data_count(db_session, stock_id=stock2.id)
    assert stock2_count == 1


@pytest.mark.asyncio
async def test_get_stocks_with_stale_data(db_session):
    """Test getting stocks with stale data (data freshness tracking)"""
    # Create stocks
    stock1 = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    stock2 = await create_stock(
        session=db_session,
        symbol="MSFT",
        company_name="Microsoft Corporation",
    )
    
    stock3 = await create_stock(
        session=db_session,
        symbol="GOOGL",
        company_name="Alphabet Inc.",
    )
    
    now = datetime.now(timezone.utc)
    
    # Stock1: Fresh data (within 1 hour)
    await create_market_data(
        session=db_session,
        stock_id=stock1.id,
        price=150.00,
        volume=1000000,
        timestamp=now - timedelta(minutes=30),
    )
    
    # Stock2: Stale data (older than 1 hour)
    await create_market_data(
        session=db_session,
        stock_id=stock2.id,
        price=300.00,
        volume=2000000,
        timestamp=now - timedelta(hours=2),
    )
    
    # Stock3: No data (should be included in stale list)
    
    # Get stale stocks (max_age_hours=1)
    stale_stocks = await get_stocks_with_stale_data(db_session, max_age_hours=1)
    
    # Should return stock2 (stale) and stock3 (no data)
    stale_ids = [stock_id for stock_id, _ in stale_stocks]
    assert stock1.id not in stale_ids  # Fresh data
    assert stock2.id in stale_ids  # Stale data
    assert stock3.id in stale_ids  # No data

