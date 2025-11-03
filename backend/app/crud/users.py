"""CRUD operations for user preferences and tier"""
from __future__ import annotations

from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_preferences import UserPreferences
from app.models.enums import HoldingPeriodEnum, RiskToleranceEnum, TierEnum
from app.schemas.user_preferences import UserPreferencesUpdate
from app.users.models import User


async def get_user_preferences(
    session: AsyncSession, user_id: UUID
) -> UserPreferences | None:
    """Get user preferences by user_id"""
    result = await session.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_user_preferences(
    session: AsyncSession,
    user_id: UUID,
    preferences: UserPreferencesUpdate,
) -> UserPreferences:
    """Create or update user preferences"""
    # Try to get existing preferences
    existing = await get_user_preferences(session, user_id)
    
    if existing:
        # Update existing preferences
        if preferences.holding_period is not None:
            existing.holding_period = preferences.holding_period
        if preferences.risk_tolerance is not None:
            existing.risk_tolerance = preferences.risk_tolerance
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        # Create new preferences
        # Use provided values or defaults from enums
        new_preferences = UserPreferences(
            id=uuid4(),
            user_id=user_id,
            holding_period=preferences.holding_period or HoldingPeriodEnum.DAILY,
            risk_tolerance=preferences.risk_tolerance or RiskToleranceEnum.MEDIUM,
        )
        session.add(new_preferences)
        await session.commit()
        await session.refresh(new_preferences)
        return new_preferences


async def get_user_tier(
    session: AsyncSession, user_id: UUID
) -> TierEnum | None:
    """Get user tier by user_id"""
    result = await session.execute(
        select(User.tier).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

