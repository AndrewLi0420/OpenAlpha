"""CRUD operations for stocks"""
from __future__ import annotations

from uuid import UUID, uuid4
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock


async def get_stock_by_symbol(
    session: AsyncSession, symbol: str
) -> Stock | None:
    """Get stock by symbol (case-insensitive)"""
    result = await session.execute(
        select(Stock).where(func.upper(Stock.symbol) == symbol.upper())
    )
    return result.scalar_one_or_none()


async def get_stock_by_name(
    session: AsyncSession, name: str
) -> Stock | None:
    """Get stock by exact company name match"""
    result = await session.execute(
        select(Stock).where(Stock.company_name == name)
    )
    return result.scalar_one_or_none()


async def search_stocks(
    session: AsyncSession, query: str, limit: int = 50
) -> list[Stock]:
    """Search stocks by symbol or company name (partial match)"""
    search_pattern = f"%{query}%"
    result = await session.execute(
        select(Stock)
        .where(
            (Stock.symbol.ilike(search_pattern))
            | (Stock.company_name.ilike(search_pattern))
        )
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_all_stocks(
    session: AsyncSession
) -> list[Stock]:
    """Get all stocks"""
    result = await session.execute(select(Stock))
    return list(result.scalars().all())


async def get_stock_count(
    session: AsyncSession
) -> int:
    """Get total count of stocks"""
    result = await session.execute(select(func.count(Stock.id)))
    return result.scalar_one() or 0


async def create_stock(
    session: AsyncSession,
    symbol: str,
    company_name: str,
    sector: str | None = None,
    fortune_500_rank: int | None = None,
) -> Stock:
    """Create a new stock"""
    stock = Stock(
        id=uuid4(),
        symbol=symbol.upper(),
        company_name=company_name,
        sector=sector,
        fortune_500_rank=fortune_500_rank,
    )
    session.add(stock)
    await session.commit()
    await session.refresh(stock)
    return stock


async def upsert_stock(
    session: AsyncSession,
    symbol: str,
    company_name: str,
    sector: str | None = None,
    fortune_500_rank: int | None = None,
) -> Stock:
    """Create or update stock (idempotent import)"""
    # Try to get existing stock
    existing = await get_stock_by_symbol(session, symbol)
    
    if existing:
        # Update existing stock
        existing.company_name = company_name
        if sector is not None:
            existing.sector = sector
        if fortune_500_rank is not None:
            existing.fortune_500_rank = fortune_500_rank
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        # Create new stock
        return await create_stock(
            session, symbol, company_name, sector, fortune_500_rank
        )

