"""Integration-ish test for sentiment job idempotency using fixed timestamp and mocked sources"""
import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_sentiment_job_idempotent(db_session, monkeypatch):
    from uuid import uuid4
    from app.models.stock import Stock
    from app.crud.sentiment_data import get_aggregated_sentiment
    from app.tasks import sentiment as job

    # Insert a stock
    stock = Stock(id=uuid4(), symbol="IDEMP", company_name="Idempotent Inc.")
    db_session.add(stock)
    await db_session.commit()

    # Mock collectors to return deterministic results
    async def fake_collector(_symbol: str):
        return {"sentiment_score": 0.5, "source": "fake", "timestamp": datetime.now(timezone.utc)}

    monkeypatch.setattr(job, "SOURCE_FUNCS", [fake_collector, fake_collector])

    # Freeze time for idempotency by monkeypatching datetime.now in the job module
    class FixedDateTime:
        @staticmethod
        def now(tz=None):
            return datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(job, "datetime", FixedDateTime)

    # First run
    stats1 = await job.collect_sentiment_for_stocks(db_session, [stock], batch_size=1)
    assert stats1["successful"] == 1

    # Second run with same fixed time should not insert duplicate
    stats2 = await job.collect_sentiment_for_stocks(db_session, [stock], batch_size=1)
    assert stats2["successful"] == 1  # processed, but should not double-insert

    # Check aggregated sentiment exists and is stable
    agg = await get_aggregated_sentiment(db_session, stock.id)
    assert agg is not None
    assert abs(agg - 0.5) < 1e-6


