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


