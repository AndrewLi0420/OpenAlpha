"""Unit tests for tier service"""
import pytest
import pytest_asyncio
from uuid import uuid4

from app.services.tier_service import get_user_tier, check_tier_limit
from app.models.user_stock_tracking import UserStockTracking
from app.models.stock import Stock
from app.users.models import User
from app.models.enums import TierEnum


@pytest_asyncio.fixture
async def test_user_free(db_session):
    """Create a test user with FREE tier"""
    user = User(
        id=uuid4(),
        email="free@example.com",
        hashed_password="$2b$12$dummyhash",
        tier=TierEnum.FREE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_premium(db_session):
    """Create a test user with PREMIUM tier"""
    user = User(
        id=uuid4(),
        email="premium@example.com",
        hashed_password="$2b$12$dummyhash",
        tier=TierEnum.PREMIUM,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_stock(db_session):
    """Create a test stock"""
    stock = Stock(
        id=uuid4(),
        symbol="TEST",
        company_name="Test Company",
    )
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)
    return stock


@pytest.mark.asyncio
async def test_get_user_tier_free(db_session, test_user_free):
    """Test get_user_tier returns FREE tier for free user"""
    tier = await get_user_tier(db_session, test_user_free.id)
    assert tier == TierEnum.FREE


@pytest.mark.asyncio
async def test_get_user_tier_premium(db_session, test_user_premium):
    """Test get_user_tier returns PREMIUM tier for premium user"""
    tier = await get_user_tier(db_session, test_user_premium.id)
    assert tier == TierEnum.PREMIUM


@pytest.mark.asyncio
async def test_get_user_tier_nonexistent(db_session):
    """Test get_user_tier returns FREE as default for nonexistent user"""
    fake_id = uuid4()
    tier = await get_user_tier(db_session, fake_id)
    assert tier == TierEnum.FREE  # Default fallback


@pytest.mark.asyncio
async def test_check_tier_limit_free_zero_stocks(db_session, test_user_free):
    """Test check_tier_limit: Free tier with 0 stocks (allowed, remaining: 5)"""
    result = await check_tier_limit(db_session, test_user_free.id)
    
    assert result['allowed'] is True
    assert result['limit'] == 5
    assert result['remaining'] == 5
    assert result['stock_count'] == 0


@pytest.mark.asyncio
async def test_check_tier_limit_free_four_stocks(db_session, test_user_free, test_stock):
    """Test check_tier_limit: Free tier with 4 stocks (allowed, remaining: 1)"""
    # Create 4 tracked stocks
    for i in range(4):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=test_user_free.id,
            stock_id=test_stock.id,  # Using same stock for simplicity
        )
        db_session.add(tracking)
    await db_session.commit()
    
    result = await check_tier_limit(db_session, test_user_free.id)
    
    assert result['allowed'] is True
    assert result['limit'] == 5
    assert result['remaining'] == 1
    assert result['stock_count'] == 4


@pytest.mark.asyncio
async def test_check_tier_limit_free_five_stocks(db_session, test_user_free, test_stock):
    """Test check_tier_limit: Free tier with 5 stocks (not allowed, limit reached)"""
    # Create 5 tracked stocks
    for i in range(5):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=test_user_free.id,
            stock_id=test_stock.id,
        )
        db_session.add(tracking)
    await db_session.commit()
    
    result = await check_tier_limit(db_session, test_user_free.id)
    
    assert result['allowed'] is False
    assert result['reason'] == 'free_tier_limit_reached'
    assert result['limit'] == 5
    assert result['remaining'] == 0
    assert result['stock_count'] == 5


@pytest.mark.asyncio
async def test_check_tier_limit_premium_unlimited(db_session, test_user_premium, test_stock):
    """Test check_tier_limit: Premium tier (allowed, unlimited)"""
    # Create 10 tracked stocks (exceeds free limit)
    for i in range(10):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=test_user_premium.id,
            stock_id=test_stock.id,
        )
        db_session.add(tracking)
    await db_session.commit()
    
    result = await check_tier_limit(db_session, test_user_premium.id)
    
    assert result['allowed'] is True
    assert result['limit'] is None
    assert result['remaining'] is None
    assert result['stock_count'] == 10


@pytest.mark.asyncio
async def test_check_tier_limit_premium_zero_stocks(db_session, test_user_premium):
    """Test check_tier_limit: Premium tier with 0 stocks (allowed, unlimited)"""
    result = await check_tier_limit(db_session, test_user_premium.id)
    
    assert result['allowed'] is True
    assert result['limit'] is None
    assert result['remaining'] is None
    assert result['stock_count'] == 0

