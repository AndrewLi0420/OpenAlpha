"""Unit tests for sentiment service utilities (aggregation)"""
import pytest

from app.services.sentiment_service import aggregate_sentiment_scores


def test_aggregate_sentiment_scores_basic():
    records = [
        {"sentiment_score": 0.2, "source": "s1"},
        {"sentiment_score": 0.8, "source": "s2"},
    ]
    agg = aggregate_sentiment_scores(records)
    assert agg is not None
    assert abs(agg["sentiment_score"] - 0.5) < 1e-6
    assert agg["source_count"] == 2
    assert set(agg["sources"]) == {"s1", "s2"}


