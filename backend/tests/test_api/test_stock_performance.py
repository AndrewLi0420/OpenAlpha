"""Performance tests for stock lookup operations"""
import pytest
import time

from app.crud.stocks import (
    get_stock_by_symbol,
    get_stock_by_name,
    get_all_stocks,
    create_stock,
)


@pytest.mark.asyncio
async def test_symbol_lookup_performance(db_session):
    """Test symbol lookup completes <100ms"""
    # Create test stock
    await create_stock(
        session=db_session,
        symbol="TEST",
        company_name="Test Company Inc.",
    )
    
    # Measure lookup time
    start = time.time()
    stock = await get_stock_by_symbol(db_session, "TEST")
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds
    
    assert stock is not None
    assert elapsed < 100, f"Symbol lookup took {elapsed:.2f}ms, expected <100ms"


@pytest.mark.asyncio
async def test_name_search_performance(db_session):
    """Test name search completes <200ms"""
    # Create test stock
    await create_stock(
        session=db_session,
        symbol="TEST",
        company_name="Test Company Inc.",
    )
    
    # Measure search time
    from app.crud.stocks import search_stocks
    
    start = time.time()
    results = await search_stocks(db_session, "Test")
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds
    
    assert len(results) >= 1
    assert elapsed < 200, f"Name search took {elapsed:.2f}ms, expected <200ms"


@pytest.mark.asyncio
async def test_bulk_lookup_performance(db_session):
    """Test bulk lookup (all stocks) completes <500ms"""
    # Create multiple test stocks (simulating 500 stocks)
    for i in range(50):  # Create 50 for testing (500 would be too slow in test)
        await create_stock(
            session=db_session,
            symbol=f"TEST{i:03d}",
            company_name=f"Test Company {i} Inc.",
        )
    
    # Measure bulk fetch time
    start = time.time()
    all_stocks = await get_all_stocks(db_session)
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds
    
    assert len(all_stocks) >= 50
    # For 50 stocks, should be much faster than 500ms
    # Actual 500 stocks target is <500ms
    assert elapsed < 500, f"Bulk lookup took {elapsed:.2f}ms, expected <500ms"


@pytest.mark.asyncio
async def test_symbol_index_usage(db_session):
    """Test that symbol lookup uses index efficiently"""
    # Create stock
    await create_stock(
        session=db_session,
        symbol="INDEX_TEST",
        company_name="Index Test Company",
    )
    
    # Multiple lookups should be fast (index usage)
    times = []
    for _ in range(10):
        start = time.time()
        await get_stock_by_symbol(db_session, "INDEX_TEST")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    # Average should be fast
    avg_time = sum(times) / len(times)
    assert avg_time < 50, f"Average lookup time {avg_time:.2f}ms suggests index not used efficiently"


@pytest.mark.asyncio
async def test_case_insensitive_lookup_performance(db_session):
    """Test case-insensitive lookup performance"""
    await create_stock(
        session=db_session,
        symbol="PERF",
        company_name="Performance Test Inc.",
    )
    
    # Test various case combinations
    test_cases = ["PERF", "perf", "Perf", "PeRf"]
    
    for case in test_cases:
        start = time.time()
        stock = await get_stock_by_symbol(db_session, case)
        elapsed = (time.time() - start) * 1000
        
        assert stock is not None
        assert elapsed < 100, f"Case-insensitive lookup '{case}' took {elapsed:.2f}ms"

