"""Tests for Stock model"""
import pytest
from uuid import uuid4

from app.models.stock import Stock


@pytest.mark.asyncio
async def test_stock_creation(db_session):
    """Test creating a stock"""
    stock = Stock(
        id=uuid4(),
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        fortune_500_rank=1,
    )
    
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)
    
    assert stock.symbol == "AAPL"
    assert stock.company_name == "Apple Inc."
    assert stock.sector == "Technology"
    assert stock.fortune_500_rank == 1


@pytest.mark.asyncio
async def test_stock_unique_symbol(db_session):
    """Test that stock symbol must be unique"""
    stock1 = Stock(
        id=uuid4(),
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    stock2 = Stock(
        id=uuid4(),
        symbol="AAPL",
        company_name="Apple Inc. Duplicate",
    )
    
    db_session.add(stock1)
    await db_session.commit()
    
    db_session.add(stock2)
    # This should fail due to unique constraint
    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()

