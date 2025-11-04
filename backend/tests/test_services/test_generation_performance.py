"""Performance test for scheduled generation path (lightweight)"""
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User
from app.models.enums import TierEnum
from app.crud.stocks import create_stock
from app.crud.market_data import create_market_data
from app.crud.sentiment_data import upsert_sentiment_data
from app.tasks.recommendations import scheduled_generation
from app.models.enums import RiskLevelEnum
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_scheduled_generation_under_latency_target(db_session: AsyncSession):
    # Seed user and a few stocks with minimal data
    user = User(id=uuid4(), email="perf@test.com", password_hash="x", tier=TierEnum.FREE)
    db_session.add(user)
    await db_session.commit()

    stocks = []
    for sym in ("PERF1", "PERF2", "PERF3"):
        s = await create_stock(db_session, symbol=sym, company_name=f"{sym} Inc")
        stocks.append(s)

        # minimal recent history
        now = datetime.now(timezone.utc)
        for i in range(10):
            ts = now - timedelta(days=10 - i)
            await create_market_data(db_session, stock_id=s.id, price=100 + i, volume=1000 + i, timestamp=ts)
            await upsert_sentiment_data(db_session, stock_id=s.id, sentiment_score=0.1, source="web_aggregate", timestamp=ts)

    # Patch heavy pieces to be fast
    async def fast_predict_stock(session, stock_id, use_ensemble=True):
        return {"signal": "buy", "confidence_score": 0.9}

    async def fast_calc_vol(session, stock_id, days=30):
        return 0.1

    async def fast_calc_risk(session, stock_id, ml_confidence, market_conditions=None):
        return RiskLevelEnum.LOW

    # Avoid actual DB writes for performance measurement
    db_session.add = MagicMock()
    db_session.commit = AsyncMock(return_value=None)
    db_session.refresh = AsyncMock(return_value=None)

    start = time.time()
    with patch("app.services.recommendation_service.predict_stock", side_effect=fast_predict_stock), \
         patch("app.services.recommendation_service.calculate_volatility", side_effect=fast_calc_vol), \
         patch("app.services.recommendation_service.calculate_risk_level", side_effect=fast_calc_risk), \
         patch("app.services.recommendation_service.Recommendation"):
        created = await scheduled_generation(db_session, user_id=user.id, daily_target_count=3)

    elapsed = time.time() - start
    assert created == 3
    assert elapsed < 1.0  # well under 60s SLA in test harness


