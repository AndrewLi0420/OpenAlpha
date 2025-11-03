"""Tests for stock CRUD operations"""
import pytest
from uuid import uuid4

# Import models to ensure relationships are registered
from app.models import Stock  # noqa: F401
from app.crud.stocks import (
    get_stock_by_symbol,
    get_stock_by_name,
    search_stocks,
    get_all_stocks,
    get_stock_count,
    create_stock,
    upsert_stock,
)


@pytest.mark.asyncio
async def test_create_stock(db_session):
    """Test creating a stock"""
    stock = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        fortune_500_rank=1,
    )
    
    assert stock.symbol == "AAPL"
    assert stock.company_name == "Apple Inc."
    assert stock.sector == "Technology"
    assert stock.fortune_500_rank == 1
    assert stock.id is not None


@pytest.mark.asyncio
async def test_get_stock_by_symbol(db_session):
    """Test getting stock by symbol (case-insensitive)"""
    # Create stock
    await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    # Test case-insensitive lookup
    stock1 = await get_stock_by_symbol(db_session, "AAPL")
    assert stock1 is not None
    assert stock1.symbol == "AAPL"
    
    stock2 = await get_stock_by_symbol(db_session, "aapl")
    assert stock2 is not None
    assert stock2.symbol == "AAPL"
    
    # Test non-existent symbol
    stock3 = await get_stock_by_symbol(db_session, "NONEXISTENT")
    assert stock3 is None


@pytest.mark.asyncio
async def test_get_stock_by_name(db_session):
    """Test getting stock by company name"""
    await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
    )
    
    stock = await get_stock_by_name(db_session, "Apple Inc.")
    assert stock is not None
    assert stock.company_name == "Apple Inc."
    
    # Test non-existent name
    stock2 = await get_stock_by_name(db_session, "Non-existent Company")
    assert stock2 is None


@pytest.mark.asyncio
async def test_search_stocks(db_session):
    """Test searching stocks by symbol or name"""
    # Create multiple stocks
    await create_stock(db_session, "AAPL", "Apple Inc.", "Technology")
    await create_stock(db_session, "MSFT", "Microsoft Corporation", "Technology")
    await create_stock(db_session, "JPM", "JPMorgan Chase & Co.", "Financials")
    
    # Search by symbol
    results = await search_stocks(db_session, "AAP")
    assert len(results) == 1
    assert results[0].symbol == "AAPL"
    
    # Search by company name
    results = await search_stocks(db_session, "Microsoft")
    assert len(results) == 1
    assert results[0].symbol == "MSFT"
    
    # Search partial match
    results = await search_stocks(db_session, "Inc")
    assert len(results) >= 1  # At least Apple Inc.
    
    # Case-insensitive search
    results = await search_stocks(db_session, "apple")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_get_all_stocks(db_session):
    """Test getting all stocks"""
    # Create multiple stocks
    await create_stock(db_session, "AAPL", "Apple Inc.")
    await create_stock(db_session, "MSFT", "Microsoft Corporation")
    
    stocks = await get_all_stocks(db_session)
    assert len(stocks) >= 2
    
    symbols = {s.symbol for s in stocks}
    assert "AAPL" in symbols
    assert "MSFT" in symbols


@pytest.mark.asyncio
async def test_get_stock_count(db_session):
    """Test getting stock count"""
    initial_count = await get_stock_count(db_session)
    
    await create_stock(db_session, "AAPL", "Apple Inc.")
    assert await get_stock_count(db_session) == initial_count + 1
    
    await create_stock(db_session, "MSFT", "Microsoft Corporation")
    assert await get_stock_count(db_session) == initial_count + 2


@pytest.mark.asyncio
async def test_upsert_stock_create(db_session):
    """Test upsert_stock creates new stock"""
    stock = await upsert_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        fortune_500_rank=1,
    )
    
    assert stock.symbol == "AAPL"
    assert stock.company_name == "Apple Inc."
    assert stock.sector == "Technology"
    assert stock.fortune_500_rank == 1


@pytest.mark.asyncio
async def test_upsert_stock_update(db_session):
    """Test upsert_stock updates existing stock"""
    # Create stock
    stock1 = await create_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        fortune_500_rank=1,
    )
    
    # Update via upsert
    stock2 = await upsert_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc. Updated",
        sector="Tech",
        fortune_500_rank=3,
    )
    
    assert stock2.id == stock1.id  # Same stock
    assert stock2.company_name == "Apple Inc. Updated"
    assert stock2.sector == "Tech"
    assert stock2.fortune_500_rank == 3


@pytest.mark.asyncio
async def test_upsert_stock_case_insensitive(db_session):
    """Test upsert_stock handles case-insensitive symbols"""
    # Create with lowercase
    stock1 = await upsert_stock(
        session=db_session,
        symbol="aapl",
        company_name="Apple Inc.",
    )
    
    assert stock1.symbol == "AAPL"  # Should be uppercased
    
    # Update with uppercase
    stock2 = await upsert_stock(
        session=db_session,
        symbol="AAPL",
        company_name="Apple Inc. Updated",
    )
    
    assert stock2.id == stock1.id  # Same stock, updated
    assert stock2.symbol == "AAPL"

