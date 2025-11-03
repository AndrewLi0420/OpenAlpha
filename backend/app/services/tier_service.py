"""Tier service for freemium tier enforcement"""
from __future__ import annotations

from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TierEnum
from app.models.user_stock_tracking import UserStockTracking
from app.users.models import User
from app.core.logger import logger


async def get_user_tier(session: AsyncSession, user_id: UUID) -> TierEnum:
    """Get user tier from database"""
    result = await session.execute(
        select(User.tier).where(User.id == user_id)
    )
    tier = result.scalar_one_or_none()
    if tier is None:
        # Default to FREE if user not found (shouldn't happen in normal flow)
        logger.warning("User not found for tier check", extra={"user_id": str(user_id)})
        return TierEnum.FREE
    return tier


async def check_tier_limit(session: AsyncSession, user_id: UUID) -> dict:
    """
    Check if user can add more stocks based on their tier.
    
    Returns:
        dict with keys:
        - allowed: bool - Whether user can add more stocks
        - reason: str (optional) - Reason if not allowed ('free_tier_limit_reached')
        - limit: int | None - Stock limit (5 for free tier, None for premium)
        - remaining: int | None - Remaining slots for free tier, None for premium
        - stock_count: int - Current number of stocks tracked
    """
    try:
        # Get user tier
        tier = await get_user_tier(session, user_id)
        
        # Count current tracked stocks
        count_result = await session.execute(
            select(func.count(UserStockTracking.id)).where(
                UserStockTracking.user_id == user_id
            )
        )
        stock_count = count_result.scalar_one() or 0
        
        # Premium tier: unlimited access
        if tier == TierEnum.PREMIUM:
            result = {
                'allowed': True,
                'limit': None,
                'remaining': None,
                'stock_count': stock_count,
            }
            logger.info(
                "Tier check - Premium user",
                extra={
                    "user_id": str(user_id),
                    "tier": tier.value,
                    "result": result
                }
            )
            return result
        
        # Free tier: check limit
        FREE_TIER_LIMIT = 5
        if stock_count >= FREE_TIER_LIMIT:
            result = {
                'allowed': False,
                'reason': 'free_tier_limit_reached',
                'limit': FREE_TIER_LIMIT,
                'remaining': 0,
                'stock_count': stock_count,
            }
            logger.info(
                "Tier check - Free tier limit reached",
                extra={
                    "user_id": str(user_id),
                    "tier": tier.value,
                    "stock_count": stock_count,
                    "result": result
                }
            )
            return result
        
        # Free tier: under limit
        remaining = FREE_TIER_LIMIT - stock_count
        result = {
            'allowed': True,
            'limit': FREE_TIER_LIMIT,
            'remaining': remaining,
            'stock_count': stock_count,
        }
        logger.info(
            "Tier check - Free tier under limit",
            extra={
                "user_id": str(user_id),
                "tier": tier.value,
                "stock_count": stock_count,
                "remaining": remaining,
                "result": result
            }
        )
        return result
        
    except Exception as e:
        logger.error(
            "Tier check failed",
            extra={"user_id": str(user_id), "error": str(e)},
            exc_info=True
        )
        # Fail safe: deny access on error
        return {
            'allowed': False,
            'reason': 'tier_check_error',
            'stock_count': 0,
        }

