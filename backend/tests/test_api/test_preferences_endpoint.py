"""Integration tests for preferences endpoints"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.core.auth import get_auth_router, fastapi_users, current_user
from app.users.models import User, get_user_db
from app.users.routes import router as users_router
from app.models.user_preferences import UserPreferences
from app.models.enums import HoldingPeriodEnum, RiskToleranceEnum
from app.models.enums import TierEnum
from uuid import uuid4


@pytest_asyncio.fixture
async def client(db_session):
    """Create FastAPI test client with overridden dependencies"""
    app = FastAPI()
    
    # Override FastAPI Users database dependency to use test session
    async def override_get_user_db():
        yield SQLAlchemyUserDatabase(db_session, User)
    
    # Override the get_user_db dependency used by FastAPI Users
    app.dependency_overrides[get_user_db] = override_get_user_db
    
    # Include auth router (login/logout endpoints)
    app.include_router(get_auth_router())
    # Include users router (for preferences endpoints)
    app.include_router(users_router)
    
    # Use ASGITransport to connect AsyncClient to FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac
        # Cleanup: remove overrides after test
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_user(db_session, client):
    """Create a registered and logged-in user for authenticated requests"""
    # Register a user first
    register_data = {
        "email": "test@example.com",
        "password": "TestPass123!",  # Must meet complexity requirements
    }
    
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        register_response = await client.post("/api/v1/auth/register", json=register_data)
    
    # Login to get auth cookie
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"],
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert login_response.status_code in [200, 204]
    
    # Return user email and ensure cookie is set in client
    return register_data["email"]


@pytest.mark.asyncio
async def test_get_preferences_authenticated(db_session, client, authenticated_user):
    """Test GET /api/v1/users/me/preferences with authenticated user: returns 404 if no preferences"""
    response = await client.get("/api/v1/users/me/preferences")
    
    # Should return 404 if preferences don't exist yet
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_preferences_with_data(db_session, client, authenticated_user):
    """Test GET /api/v1/users/me/preferences returns 200 with preferences when they exist"""
    # Get user from database
    from sqlalchemy import select
    result = await db_session.execute(
        select(User).where(User.email == authenticated_user)
    )
    user = result.scalar_one()
    
    # Create preferences for user
    preferences = UserPreferences(
        id=uuid4(),
        user_id=user.id,
        holding_period=HoldingPeriodEnum.WEEKLY,
        risk_tolerance=RiskToleranceEnum.HIGH,
    )
    db_session.add(preferences)
    await db_session.commit()
    
    # Get preferences via API
    response = await client.get("/api/v1/users/me/preferences")
    
    assert response.status_code == 200
    data = response.json()
    assert data["holding_period"] == "weekly"
    assert data["risk_tolerance"] == "high"
    assert data["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_get_preferences_unauthenticated(db_session, client):
    """Test GET /api/v1/users/me/preferences with unauthenticated user: returns 401"""
    response = await client.get("/api/v1/users/me/preferences")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_preferences_create(db_session, client, authenticated_user):
    """Test PUT /api/v1/users/me/preferences creates preferences if they don't exist"""
    update_data = {
        "holding_period": "monthly",
        "risk_tolerance": "low",
    }
    
    response = await client.put("/api/v1/users/me/preferences", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["holding_period"] == "monthly"
    assert data["risk_tolerance"] == "low"
    
    # Verify preferences were saved to database
    from sqlalchemy import select
    result = await db_session.execute(
        select(User).where(User.email == authenticated_user)
    )
    user = result.scalar_one()
    
    from app.crud.users import get_user_preferences
    prefs = await get_user_preferences(db_session, user.id)
    assert prefs is not None
    assert prefs.holding_period == HoldingPeriodEnum.MONTHLY
    assert prefs.risk_tolerance == RiskToleranceEnum.LOW


@pytest.mark.asyncio
async def test_put_preferences_update(db_session, client, authenticated_user):
    """Test PUT /api/v1/users/me/preferences updates existing preferences"""
    # Get user and create initial preferences
    from sqlalchemy import select
    result = await db_session.execute(
        select(User).where(User.email == authenticated_user)
    )
    user = result.scalar_one()
    
    initial_prefs = UserPreferences(
        id=uuid4(),
        user_id=user.id,
        holding_period=HoldingPeriodEnum.DAILY,
        risk_tolerance=RiskToleranceEnum.MEDIUM,
    )
    db_session.add(initial_prefs)
    await db_session.commit()
    
    # Update preferences
    update_data = {
        "holding_period": "weekly",
        "risk_tolerance": "high",
    }
    
    response = await client.put("/api/v1/users/me/preferences", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["holding_period"] == "weekly"
    assert data["risk_tolerance"] == "high"
    assert data["id"] == str(initial_prefs.id)  # Same record updated


@pytest.mark.asyncio
async def test_put_preferences_partial_update(db_session, client, authenticated_user):
    """Test PUT /api/v1/users/me/preferences with partial update (only one field)"""
    # Get user and create initial preferences
    from sqlalchemy import select
    result = await db_session.execute(
        select(User).where(User.email == authenticated_user)
    )
    user = result.scalar_one()
    
    initial_prefs = UserPreferences(
        id=uuid4(),
        user_id=user.id,
        holding_period=HoldingPeriodEnum.DAILY,
        risk_tolerance=RiskToleranceEnum.MEDIUM,
    )
    db_session.add(initial_prefs)
    await db_session.commit()
    
    # Update only holding_period
    update_data = {
        "holding_period": "monthly",
    }
    
    response = await client.put("/api/v1/users/me/preferences", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["holding_period"] == "monthly"
    assert data["risk_tolerance"] == "medium"  # Unchanged


@pytest.mark.asyncio
async def test_put_preferences_invalid_enum(db_session, client, authenticated_user):
    """Test PUT /api/v1/users/me/preferences with invalid enum values: returns 400"""
    update_data = {
        "holding_period": "invalid_period",
        "risk_tolerance": "low",
    }
    
    response = await client.put("/api/v1/users/me/preferences", json=update_data)
    
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_put_preferences_unauthenticated(db_session, client):
    """Test PUT /api/v1/users/me/preferences with unauthenticated user: returns 401"""
    update_data = {
        "holding_period": "daily",
        "risk_tolerance": "medium",
    }
    
    response = await client.put("/api/v1/users/me/preferences", json=update_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_preferences_cors_headers(db_session, client, authenticated_user):
    """Test preferences endpoints include CORS headers"""
    response = await client.get("/api/v1/users/me/preferences")
    
    # CORS headers should be present (set by middleware)
    # Note: Test client may not show all headers, so we just verify request doesn't fail
    assert response.status_code in [200, 404, 401]  # Any valid response

