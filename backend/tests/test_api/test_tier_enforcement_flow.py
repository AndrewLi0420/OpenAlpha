"""Integration tests for complete tier enforcement flow (E2E simulation)

Tests the complete user journey:
- Free tier user tracking stocks up to limit
- Tier status updates correctly as stocks are added
- Premium user bypasses limit checks
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from uuid import uuid4
from sqlalchemy import select

from app.core.auth import get_auth_router, fastapi_users
from app.users.models import User, get_user_db
from app.users.routes import router as users_router
from app.models.enums import TierEnum
from app.models.user_stock_tracking import UserStockTracking
from app.models.stock import Stock
from app.core.tier import require_tier_access


@pytest_asyncio.fixture
async def client(db_session):
    """Create FastAPI test client"""
    app = FastAPI()
    
    async def override_get_user_db():
        yield SQLAlchemyUserDatabase(db_session, User)
    
    app.dependency_overrides[get_user_db] = override_get_user_db
    
    app.include_router(get_auth_router())
    app.include_router(users_router)
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_user(db_session, client):
    """Create and authenticate a free tier user"""
    from unittest.mock import AsyncMock, patch
    
    register_data = {
        "email": f"test-{uuid4()}@example.com",
        "password": "TestPass123!",
    }
    
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        await client.post("/api/v1/auth/register", json=register_data)
    
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"],
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert login_response.status_code in [200, 204]
    
    # Get user from database
    result = await db_session.execute(
        select(User).where(User.email == register_data["email"])
    )
    user = result.scalar_one()
    
    return {
        "email": register_data["email"],
        "password": register_data["password"],
        "user": user,
        "cookies": login_response.cookies,
    }


@pytest_asyncio.fixture
async def premium_user(db_session, client, authenticated_user):
    """Upgrade user to premium tier"""
    authenticated_user["user"].tier = TierEnum.PREMIUM
    await db_session.commit()
    await db_session.refresh(authenticated_user["user"])
    return authenticated_user


@pytest_asyncio.fixture
async def test_stocks(db_session):
    """Create multiple test stocks"""
    stocks = []
    for i in range(10):
        stock = Stock(
            id=uuid4(),
            symbol=f"TEST{i}",
            company_name=f"Test Company {i}",
        )
        db_session.add(stock)
        stocks.append(stock)
    await db_session.commit()
    for stock in stocks:
        await db_session.refresh(stock)
    return stocks


@pytest.mark.asyncio
async def test_complete_flow_free_tier_user_tracks_stocks_up_to_limit(
    db_session, client, authenticated_user, test_stocks
):
    """[E2E Simulation] Test complete flow: Free tier user tracks stocks up to limit"""
    user = authenticated_user["user"]
    cookies = authenticated_user["cookies"]
    
    # Step 1: User starts with 0 stocks - tier status shows can_add_more=True
    response = await client.get(
        "/api/v1/users/me/tier-status",
        cookies=cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["stock_count"] == 0
    assert data["stock_limit"] == 5
    assert data["can_add_more"] is True
    
    # Step 2: User tracks first stock (simulating via database)
    tracking1 = UserStockTracking(
        id=uuid4(),
        user_id=user.id,
        stock_id=test_stocks[0].id,
    )
    db_session.add(tracking1)
    await db_session.commit()
    
    # Step 3: Tier status updates correctly
    response = await client.get(
        "/api/v1/users/me/tier-status",
        cookies=cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stock_count"] == 1
    assert data["can_add_more"] is True
    assert data["remaining"] == 4 if "remaining" in data else data["stock_limit"] - data["stock_count"] == 4
    
    # Step 4: User tracks 4 more stocks (total 5)
    for i in range(1, 5):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=user.id,
            stock_id=test_stocks[i].id,
        )
        db_session.add(tracking)
    await db_session.commit()
    
    # Step 5: Tier status shows limit reached
    response = await client.get(
        "/api/v1/users/me/tier-status",
        cookies=cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["stock_count"] == 5
    assert data["stock_limit"] == 5
    assert data["can_add_more"] is False  # Limit reached
    
    # Step 6: Attempt to track 6th stock should be blocked (would be done via API endpoint in Epic 3)
    # For now, verify tier check would block it
    from app.services.tier_service import check_tier_limit
    tier_check = await check_tier_limit(db_session, user.id)
    assert tier_check["allowed"] is False
    assert tier_check["reason"] == "free_tier_limit_reached"
    assert tier_check["stock_count"] == 5


@pytest.mark.asyncio
async def test_premium_user_can_track_unlimited_stocks(
    db_session, client, premium_user, test_stocks
):
    """[E2E Simulation] Test premium user: Can track unlimited stocks without prompts"""
    user = premium_user["user"]
    cookies = premium_user["cookies"]
    
    # Step 1: Premium user starts with 0 stocks
    response = await client.get(
        "/api/v1/users/me/tier-status",
        cookies=cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "premium"
    assert data["stock_limit"] is None  # Unlimited
    assert data["can_add_more"] is True
    
    # Step 2: Track 10 stocks (exceeds free tier limit)
    for i in range(10):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=user.id,
            stock_id=test_stocks[i].id,
        )
        db_session.add(tracking)
    await db_session.commit()
    
    # Step 3: Tier status shows unlimited access
    response = await client.get(
        "/api/v1/users/me/tier-status",
        cookies=cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "premium"
    assert data["stock_count"] == 10
    assert data["stock_limit"] is None
    assert data["can_add_more"] is True  # Can always add more as premium
    
    # Step 4: Tier check allows unlimited tracking
    from app.services.tier_service import check_tier_limit
    tier_check = await check_tier_limit(db_session, user.id)
    assert tier_check["allowed"] is True
    assert tier_check["limit"] is None
    assert tier_check["stock_count"] == 10


@pytest.mark.asyncio
async def test_tier_status_display_updates_correctly_on_profile(
    db_session, client, authenticated_user, test_stocks
):
    """[E2E Simulation] Test tier status display: Profile shows correct tier indicator"""
    user = authenticated_user["user"]
    cookies = authenticated_user["cookies"]
    
    # Step 1: Check GET /api/v1/users/me includes tier
    response = await client.get(
        "/api/v1/users/me",
        cookies=cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert data["tier"] == "free"
    
    # Step 2: Check tier-status endpoint returns correct format for Profile display
    response = await client.get(
        "/api/v1/users/me/tier-status",
        cookies=cookies
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify all fields needed for Profile UI display
    assert "tier" in data
    assert "stock_count" in data
    assert "stock_limit" in data
    assert "can_add_more" in data
    
    # Step 3: After adding stocks, status updates
    for i in range(3):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=user.id,
            stock_id=test_stocks[i].id,
        )
        db_session.add(tracking)
    await db_session.commit()
    
    response = await client.get(
        "/api/v1/users/me/tier-status",
        cookies=cookies
    )
    data = response.json()
    assert data["stock_count"] == 3
    assert data["stock_limit"] == 5
    assert data["can_add_more"] is True
    
    # Profile UI can use this data to display: "Free Tier - Tracking 3/5 stocks"

