import pytest
import pytest_asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from app.api.v1.endpoints.recommendations import router as rec_router
from app.db.config import get_db


@pytest_asyncio.fixture
async def client(db_session):
    app = FastAPI()
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    app.include_router(rec_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generate_endpoint_creates_recommendations(client):
    user_id = uuid4()

    async def mock_generate(session, user_id, daily_target_count, use_ensemble=True, market_conditions=None):
        class Fake:
            def __init__(self, stock_id):
                self.stock_id = stock_id
        return [Fake(uuid4()) for _ in range(3)]

    with patch("app.api.v1.endpoints.recommendations.generate_recommendations", side_effect=mock_generate):
        resp = await client.post(f"/api/v1/recommendations/generate?user_id={user_id}&count=3")
        assert resp.status_code == 202
        data = resp.json()
        assert data["created"] == 3


