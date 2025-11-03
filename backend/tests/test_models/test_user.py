"""Tests for User model"""
import pytest
from uuid import uuid4

from app.users.models import User
from app.models.enums import TierEnum


@pytest.mark.asyncio
async def test_user_creation(db_session, test_user_data):
    """Test creating a user"""
    user = User(
        id=uuid4(),
        email=test_user_data["email"],
        password_hash="hashed_password",
        tier=test_user_data["tier"],
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.email == test_user_data["email"]
    assert user.tier == TierEnum.FREE
    assert user.id is not None


@pytest.mark.asyncio
async def test_user_tier_enum(db_session):
    """Test user tier enum values"""
    user = User(
        id=uuid4(),
        email="premium@example.com",
        password_hash="hashed_password",
        tier=TierEnum.PREMIUM,
    )
    
    db_session.add(user)
    await db_session.commit()
    
    assert user.tier == TierEnum.PREMIUM
    assert user.tier.value == "premium"

