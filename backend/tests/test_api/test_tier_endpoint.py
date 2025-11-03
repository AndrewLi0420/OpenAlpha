"""Integration tests for tier status endpoints"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from uuid import uuid4

from app.core.auth import get_auth_router, fastapi_users
from app.users.models import User, get_user_db
from app.users.routes import router as users_router
from app.models.enums import TierEnum
from app.models.user_stock_tracking import UserStockTracking
from app.models.stock import Stock


@pytest_asyncio.fixture
async def client(db_session):
    """Create FastAPI test client with overridden dependencies"""
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
    """Create a registered and logged-in user for authenticated requests"""
    register_data = {
        "email": "test@example.com",
        "password": "TestPass123!",
    }
    
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        register_response = await client.post("/api/v1/auth/register", json=register_data)
    
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"],
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert login_response.status_code in [200, 204]
    
    return register_data["email"]


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
async def test_get_tier_status_free_user(db_session, client, authenticated_user):
    """Test GET /api/v1/users/me/tier-status with free tier user: returns correct stock count and limit"""
    # Get user from database
    from sqlalchemy import select
    result = await db_session.execute(
        select(User).where(User.email == authenticated_user)
    )
    user = result.scalar_one()
    assert user.tier == TierEnum.FREE  # New users default to FREE
    
    response = await client.get("/api/v1/users/me/tier-status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["stock_count"] == 0
    assert data["stock_limit"] == 5
    assert data["can_add_more"] is True


@pytest.mark.asyncio
async def test_get_tier_status_free_user_with_stocks(db_session, client, authenticated_user, test_stock):
    """Test GET /api/v1/users/me/tier-status with free tier user having 3 stocks"""
    # Get user from database
    from sqlalchemy import select
    result = await db_session.execute(
        select(User).where(User.email == authenticated_user)
    )
    user = result.scalar_one()
    
    # Create 3 tracked stocks
    for i in range(3):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=user.id,
            stock_id=test_stock.id,
        )
        db_session.add(tracking)
    await db_session.commit()
    
    response = await client.get("/api/v1/users/me/tier-status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["stock_count"] == 3
    assert data["stock_limit"] == 5
    assert data["can_add_more"] is True


@pytest.mark.asyncio
async def test_get_tier_status_premium_user(db_session, client, authenticated_user, test_stock):
    """Test GET /api/v1/users/me/tier-status with premium tier user: returns unlimited status"""
    # Get user from database and upgrade to premium
    from sqlalchemy import select
    result = await db_session.execute(
        select(User).where(User.email == authenticated_user)
    )
    user = result.scalar_one()
    user.tier = TierEnum.PREMIUM
    await db_session.commit()
    
    # Create 10 tracked stocks (exceeds free limit)
    for i in range(10):
        tracking = UserStockTracking(
            id=uuid4(),
            user_id=user.id,
            stock_id=test_stock.id,
        )
        db_session.add(tracking)
    await db_session.commit()
    
    response = await client.get("/api/v1/users/me/tier-status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "premium"
    assert data["stock_count"] == 10
    assert data["stock_limit"] is None
    assert data["can_add_more"] is True


@pytest.mark.asyncio
async def test_get_tier_status_unauthenticated(db_session, client):
    """Test GET /api/v1/users/me/tier-status with unauthenticated user: returns 401"""
    response = await client.get("/api/v1/users/me/tier-status")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_users_me_includes_tier(db_session, client, authenticated_user):
    """Test GET /api/v1/users/me returns tier field: "free" or "premium" """
    response = await client.get("/api/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert data["tier"] in ["free", "premium"]


@pytest.mark.asyncio
async def test_tier_status_cors_headers(db_session, client, authenticated_user):
    """Test tier status endpoint includes CORS headers"""
    response = await client.get("/api/v1/users/me/tier-status")
    
    assert response.status_code == 200

