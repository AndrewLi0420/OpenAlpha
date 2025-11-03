"""Tier enforcement dependency for FastAPI endpoints"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_user
from app.db.config import get_db
from app.services.tier_service import check_tier_limit
from app.users.models import User


async def require_tier_access(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    FastAPI dependency that checks if user can add more stocks.
    
    Raises HTTPException 403 if free tier limit reached.
    Returns tier check result dict for allowed users.
    
    Usage:
        @router.post("/track-stock")
        async def track_stock(
            tier_check: dict = Depends(require_tier_access),
            ...
        ):
            # tier_check contains allowed, limit, remaining, etc.
    """
    tier_result = await check_tier_limit(session, user.id)
    
    if not tier_result.get('allowed', False):
        reason = tier_result.get('reason', 'tier_limit_reached')
        if reason == 'free_tier_limit_reached':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free tier limit reached. Upgrade for unlimited access."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tier check failed. Please try again."
            )
    
    return tier_result

