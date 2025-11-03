"""Web scraping sentiment collection and aggregation service"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup  # type: ignore

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple per-domain rate limiter enforcing a minimum delay between requests."""

    def __init__(self, min_delay_seconds: float = 2.0) -> None:
        self.min_delay_seconds = min_delay_seconds
        self._domain_to_lock: dict[str, asyncio.Lock] = {}

    async def wait(self, domain: str) -> None:
        lock = self._domain_to_lock.setdefault(domain, asyncio.Lock())
        # Serialize requests per domain; add delay between sequential calls
        async with lock:
            await asyncio.sleep(self.min_delay_seconds)


async def _load_robots_txt(client: httpx.AsyncClient, base_url: str) -> RobotFileParser | None:
    try:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        resp = await client.get(robots_url, timeout=10)
        if resp.status_code != 200:
            return None
        rp = RobotFileParser()
        rp.parse(resp.text.splitlines())
        return rp
    except Exception:
        return None


async def collect_sentiment_from_web(
    stock_symbol: str,
    source_url: str,
    *,
    user_agent: str | None = None,
    min_delay_seconds: float | None = None,
) -> dict[str, Any] | None:
    """
    Scrape a page and derive a naive sentiment score in [-1.0, 1.0].
    Returns dict with sentiment_score, source, timestamp on success; None on failure or disallowed by robots.txt.
    """
    parsed = urlparse(source_url)
    domain = parsed.netloc
    from app.core.config import settings
    effective_user_agent = user_agent or settings.SCRAPE_USER_AGENT
    effective_delay = min_delay_seconds if min_delay_seconds is not None else settings.SCRAPE_MIN_DELAY_SECONDS

    headers = {"User-Agent": effective_user_agent}
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        # robots.txt check and crawl-delay respect
        rp = await _load_robots_txt(client, source_url)
        if rp and not rp.can_fetch(effective_user_agent, source_url):
            logger.info("Robots.txt disallows scraping %s", source_url)
            return None
        # Determine crawl-delay per robots.txt if available
        if rp:
            try:
                cd = rp.crawl_delay(effective_user_agent)
                if isinstance(cd, (int, float)) and cd > 0:
                    effective_delay = float(cd)
            except Exception:
                pass
        rate_limiter = RateLimiter(min_delay_seconds=effective_delay)
        # Respect per-domain delay
        await rate_limiter.wait(domain)

        try:
            resp = await client.get(source_url, timeout=20)
            if resp.status_code != 200:
                logger.warning("Non-200 fetching %s: %s", source_url, resp.status_code)
                return None
        except httpx.HTTPError as e:
            logger.error("HTTP error fetching %s: %s", source_url, e)
            return None

    # Parse content
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        text_content = soup.get_text(" ", strip=True)
        if not text_content:
            return None
        score = _keyword_sentiment_score(text_content)
        return {
            "sentiment_score": float(score),
            "source": domain,
            "timestamp": datetime.now(timezone.utc),
        }
    except Exception as e:
        logger.error("Parse error for %s: %s", source_url, e)
        return None


def _keyword_sentiment_score(text: str) -> float:
    """Very simple keyword-based sentiment scoring; placeholder for MVP.
    Returns a score in [-1.0, 1.0].
    """
    text_lower = text.lower()
    positive_keywords = ["gain", "beat", "surge", "rally", "bullish", "up", "strong"]
    negative_keywords = ["loss", "miss", "drop", "plunge", "bearish", "down", "weak"]
    pos = sum(text_lower.count(k) for k in positive_keywords)
    neg = sum(text_lower.count(k) for k in negative_keywords)
    if pos == 0 and neg == 0:
        return 0.0
    score = (pos - neg) / max(pos + neg, 1)
    # clamp to [-1.0, 1.0]
    return max(-1.0, min(1.0, score))


async def collect_marketwatch_sentiment(stock_symbol: str) -> dict[str, Any] | None:
    # MarketWatch symbol page pattern (lowercased symbol)
    symbol_path = stock_symbol.lower()
    url = f"https://www.marketwatch.com/investing/stock/{symbol_path}"
    return await collect_sentiment_from_web(stock_symbol, url)


async def collect_seekingalpha_sentiment(stock_symbol: str) -> dict[str, Any] | None:
    # SeekingAlpha symbol page pattern (uppercase symbol)
    symbol_path = stock_symbol.upper()
    url = f"https://seekingalpha.com/symbol/{symbol_path}"
    return await collect_sentiment_from_web(stock_symbol, url)


def aggregate_sentiment_scores(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Aggregate multiple source scores with a simple average and metadata."""
    if not records:
        return None
    scores = [r["sentiment_score"] for r in records if r and "sentiment_score" in r]
    sources = [r.get("source", "unknown") for r in records if r]
    if not scores:
        return None
    avg = sum(scores) / len(scores)
    return {
        "sentiment_score": float(avg),
        "source_count": len(scores),
        "sources": list(sources),
    }


