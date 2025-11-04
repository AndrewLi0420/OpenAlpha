"""CRUD operations for sentiment data"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sentiment_data import SentimentData
async def exists_sentiment_record(
    session: AsyncSession,
    stock_id: UUID,
    source: str,
    timestamp: datetime,
) -> bool:
    result = await session.execute(
        select(func.count(SentimentData.id)).where(
            and_(
                SentimentData.stock_id == stock_id,
                SentimentData.source == source,
                SentimentData.timestamp == timestamp,
            )
        )
    )
    return (result.scalar_one() or 0) > 0



async def create_sentiment_data(
    session: AsyncSession,
    stock_id: UUID,
    sentiment_score: float,
    source: str,
    timestamp: datetime,
) -> SentimentData:
    """
    Insert a new sentiment data record with source attribution.
    """
    record = SentimentData(
        id=uuid4(),
        stock_id=stock_id,
        sentiment_score=sentiment_score,
        source=source,
        timestamp=timestamp,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def upsert_sentiment_data(
    session: AsyncSession,
    stock_id: UUID,
    sentiment_score: float,
    source: str,
    timestamp: datetime,
) -> SentimentData:
    """
    Upsert sentiment data record (insert or update if exists).
    Uses existence check with (stock_id, source, timestamp) for idempotency.
    """
    # Check if record already exists
    existing = await exists_sentiment_record(session, stock_id, source, timestamp)
    if existing:
        # Fetch existing record and return it
        result = await session.execute(
            select(SentimentData).where(
                and_(
                    SentimentData.stock_id == stock_id,
                    SentimentData.source == source,
                    SentimentData.timestamp == timestamp,
                )
            )
        )
        return result.scalar_one()
    
    # Create new record
    return await create_sentiment_data(
        session=session,
        stock_id=stock_id,
        sentiment_score=sentiment_score,
        source=source,
        timestamp=timestamp,
    )


async def get_latest_sentiment_data(
    session: AsyncSession,
    stock_id: UUID,
    source: str | None = None,
) -> SentimentData | None:
    """
    Get the most recent sentiment entry for a stock, optionally filtered by source.
    """
    query = (
        select(SentimentData)
        .where(SentimentData.stock_id == stock_id)
        .order_by(SentimentData.timestamp.desc())
        .limit(1)
    )
    if source is not None:
        query = query.where(SentimentData.source == source)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_sentiment_data_history(
    session: AsyncSession,
    stock_id: UUID,
    start_date: datetime,
    end_date: datetime,
    source: str | None = None,
) -> list[SentimentData]:
    """
    Get historical sentiment for a stock within a time window, optional by source.
    """
    conditions: list = [
        SentimentData.stock_id == stock_id,
        SentimentData.timestamp >= start_date,
        SentimentData.timestamp <= end_date,
    ]
    if source is not None:
        conditions.append(SentimentData.source == source)
    result = await session.execute(
        select(SentimentData)
        .where(and_(*conditions))
        .order_by(SentimentData.timestamp.asc())
    )
    return list(result.scalars().all())


async def get_aggregated_sentiment(
    session: AsyncSession,
    stock_id: UUID,
) -> float | None:
    """
    Compute a unified sentiment score across all sources (simple average).
    Returns None if no records exist.
    """
    result = await session.execute(
        select(func.avg(SentimentData.sentiment_score)).where(
            SentimentData.stock_id == stock_id
        )
    )
    value = result.scalar_one_or_none()
    return float(value) if value is not None else None


