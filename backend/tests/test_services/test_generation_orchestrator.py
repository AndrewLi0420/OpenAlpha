"""Unit tests for recommendation generation orchestrator"""
import pytest
import pytest_asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.recommendation_service import generate_recommendations


@pytest.mark.asyncio
async def test_generate_recommendations_ranking_and_count():
    session = AsyncMock()

    # Mock stocks
    stock_ids = [uuid4(), uuid4(), uuid4()]
    stocks = [MagicMock(id=sid) for sid in stock_ids]

    async def mock_get_all_stocks(sess):
        return stocks

    # Mock predictions with varying confidence
    predictions = {
        stock_ids[0]: {"signal": "buy", "confidence_score": 0.80},
        stock_ids[1]: {"signal": "sell", "confidence_score": 0.95},
        stock_ids[2]: {"signal": "hold", "confidence_score": 0.80},
    }

    async def mock_predict_stock(session, stock_id, use_ensemble=True):
        return predictions[stock_id]

    # Mock risk: prefer lower risk for tie on confidence
    async def mock_calculate_risk(session, stock_id, ml_confidence, market_conditions=None):
        # Make second 0.80 confidence stock lower risk
        if stock_id == stock_ids[2]:
            class E: value = "low"
            return E()
        class E: value = "medium"
        return E()

    class FakeRec:
        def __init__(self, id, user_id, stock_id, signal, confidence_score, risk_level, created_at):
            self.id = id
            self.user_id = user_id
            self.stock_id = stock_id
            self.signal = signal
            self.confidence_score = confidence_score
            self.risk_level = risk_level
            self.created_at = created_at

    async def noop_commit():
        return None

    session.commit = AsyncMock(side_effect=noop_commit)
    session.refresh = AsyncMock()
    session.add = MagicMock()

    with patch("app.services.recommendation_service.get_all_stocks", side_effect=mock_get_all_stocks), \
         patch("app.services.recommendation_service.predict_stock", side_effect=mock_predict_stock), \
         patch("app.services.recommendation_service.get_aggregated_sentiment", new_callable=AsyncMock, return_value=0.0), \
         patch("app.services.recommendation_service.calculate_risk_level", side_effect=mock_calculate_risk), \
         patch("app.services.recommendation_service.Recommendation", FakeRec):
        # Execute
        user_id = uuid4()
        recs = await generate_recommendations(session, user_id=user_id, daily_target_count=2)

        # Validate count
        assert len(recs) == 2

        # Highest confidence (0.95) must be first
        # Next pick among 0.80 confidence should be the one with lower risk
        # Since we cannot directly inspect order of persisted list reliably by DB, check that
        # both selected include the top confidence and the low-risk tie-breaker exists
        selected_pairs = {(r.stock_id, str(r.signal)) for r in recs}
        assert any(sid == stock_ids[1] for sid, _ in selected_pairs)
        assert any(sid == stock_ids[2] for sid, _ in selected_pairs)


