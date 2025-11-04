"""Tests for sentiment data CRUD operations"""
import pytest
from datetime import datetime, timezone, timedelta

from app.models import Stock, SentimentData  # noqa: F401
from app.users.models import User  # noqa: F401
from app.models.user_preferences import UserPreferences  # noqa: F401
from app.crud.stocks import create_stock
from app.crud.sentiment_data import (
    create_sentiment_data,
    get_latest_sentiment_data,
    get_sentiment_data_history,
    get_aggregated_sentiment,
    upsert_sentiment_data,
)


@pytest.mark.asyncio
async def test_create_sentiment_data(db_session):
    stock = await create_stock(session=db_session, symbol="AAPL", company_name="Apple Inc.")
    ts = datetime.now(timezone.utc)
    rec = await create_sentiment_data(
        session=db_session,
        stock_id=stock.id,
        sentiment_score=0.25,
        source="marketwatch",
        timestamp=ts,
    )
    assert rec.stock_id == stock.id
    assert float(rec.sentiment_score) == 0.25
    assert rec.source == "marketwatch"


@pytest.mark.asyncio
async def test_get_latest_sentiment_data(db_session):
    stock = await create_stock(session=db_session, symbol="MSFT", company_name="Microsoft")
    now = datetime.now(timezone.utc)
    await create_sentiment_data(db_session, stock.id, -0.1, "marketwatch", now - timedelta(hours=2))
    await create_sentiment_data(db_session, stock.id, 0.4, "seekingalpha", now - timedelta(hours=1))
    latest = await get_latest_sentiment_data(db_session, stock.id)
    assert latest is not None
    assert float(latest.sentiment_score) == 0.4


@pytest.mark.asyncio
async def test_get_sentiment_data_history(db_session):
    stock = await create_stock(session=db_session, symbol="GOOGL", company_name="Alphabet")
    base = datetime.now(timezone.utc)
    await create_sentiment_data(db_session, stock.id, 0.1, "marketwatch", base - timedelta(days=2))
    await create_sentiment_data(db_session, stock.id, 0.2, "marketwatch", base - timedelta(hours=12))
    await create_sentiment_data(db_session, stock.id, 0.3, "seekingalpha", base - timedelta(hours=6))
    await create_sentiment_data(db_session, stock.id, 0.8, "seekingalpha", base + timedelta(hours=1))
    history = await get_sentiment_data_history(db_session, stock.id, base - timedelta(days=1), base)
    assert len(history) == 2
    assert float(history[0].sentiment_score) == 0.2
    assert float(history[1].sentiment_score) == 0.3


@pytest.mark.asyncio
async def test_get_aggregated_sentiment(db_session):
    stock = await create_stock(session=db_session, symbol="AMZN", company_name="Amazon")
    now = datetime.now(timezone.utc)
    await create_sentiment_data(db_session, stock.id, 0.0, "s1", now - timedelta(hours=3))
    await create_sentiment_data(db_session, stock.id, 0.5, "s2", now - timedelta(hours=2))
    await create_sentiment_data(db_session, stock.id, 1.0, "s3", now - timedelta(hours=1))
    agg = await get_aggregated_sentiment(db_session, stock.id)
    assert agg is not None
    assert abs(agg - (0.0 + 0.5 + 1.0) / 3) < 1e-6


@pytest.mark.asyncio
async def test_upsert_sentiment_data_idempotency(db_session):
    """Test that upsert prevents duplicate records for same (stock_id, source, timestamp)."""
    stock = await create_stock(session=db_session, symbol="UPSERT", company_name="Upsert Test Inc.")
    ts = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    
    # First upsert should create a record
    rec1 = await upsert_sentiment_data(
        session=db_session,
        stock_id=stock.id,
        sentiment_score=0.5,
        source="test_source",
        timestamp=ts,
    )
    assert rec1 is not None
    assert float(rec1.sentiment_score) == 0.5
    
    # Second upsert with same (stock_id, source, timestamp) should return existing record
    rec2 = await upsert_sentiment_data(
        session=db_session,
        stock_id=stock.id,
        sentiment_score=0.7,  # Different score, but should still return existing
        source="test_source",
        timestamp=ts,
    )
    assert rec2 is not None
    assert rec2.id == rec1.id  # Same record ID
    assert float(rec2.sentiment_score) == 0.5  # Original score preserved
    
    # Different timestamp should create new record
    ts2 = ts.replace(minute=ts.minute + 1)
    rec3 = await upsert_sentiment_data(
        session=db_session,
        stock_id=stock.id,
        sentiment_score=0.8,
        source="test_source",
        timestamp=ts2,
    )
    assert rec3 is not None
    assert rec3.id != rec1.id  # Different record
    assert float(rec3.sentiment_score) == 0.8


