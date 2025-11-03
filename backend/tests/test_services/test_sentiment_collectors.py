"""Unit tests for per-source sentiment collectors"""
import pytest


@pytest.mark.asyncio
async def test_marketwatch_collector_calls_core(monkeypatch):
    from app.services import sentiment_service as svc

    called = {"args": None}

    async def fake_collect(stock_symbol: str, source_url: str, **kwargs):
        called["args"] = (stock_symbol, source_url)
        return {"sentiment_score": 0.1, "source": "marketwatch", "timestamp": None}

    monkeypatch.setattr(svc, "collect_sentiment_from_web", fake_collect)

    await svc.collect_marketwatch_sentiment("AAPL")
    assert called["args"][0] == "AAPL"
    assert "marketwatch.com" in called["args"][1]


@pytest.mark.asyncio
async def test_seekingalpha_collector_calls_core(monkeypatch):
    from app.services import sentiment_service as svc

    called = {"args": None}

    async def fake_collect(stock_symbol: str, source_url: str, **kwargs):
        called["args"] = (stock_symbol, source_url)
        return {"sentiment_score": 0.2, "source": "seekingalpha", "timestamp": None}

    monkeypatch.setattr(svc, "collect_sentiment_from_web", fake_collect)

    await svc.collect_seekingalpha_sentiment("MSFT")
    assert called["args"][0] == "MSFT"
    assert "seekingalpha.com" in called["args"][1]


