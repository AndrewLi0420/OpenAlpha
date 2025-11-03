from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page, Params, paginate
from app.core.auth import fastapi_users
from app.worker import queue
from app.core.auth import current_user
from app.db.config import get_db
from app.crud.users import get_user_preferences, upsert_user_preferences, get_user_tier
from app.schemas.user_preferences import UserPreferencesRead, UserPreferencesUpdate
from app.schemas.tier import TierStatusRead
from app.services.tier_service import check_tier_limit
from .models import User
from .schemas import UserRead, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/", response_model=Page[UserRead], dependencies=[Depends(current_user)])
async def user_list(params: Params = Depends(), session: AsyncSession = Depends(get_db)):
    """List users with pagination"""
    query = select(User).order_by(User.created_at.desc())
    return await paginate(session, query, params)


@router.get("/log-user-info")
async def log_user_info(user: User = Depends(current_user)):
    await queue.enqueue("log_user_email", user_email=user.email)


@router.get("/me/preferences", response_model=UserPreferencesRead)
async def get_preferences(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's preferences"""
    preferences = await get_user_preferences(session, user.id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found for user",
        )
    return preferences


@router.put("/me/preferences", response_model=UserPreferencesRead)
async def update_preferences(
    preferences_update: UserPreferencesUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update current user's preferences (creates if doesn't exist)"""
    updated_preferences = await upsert_user_preferences(
        session, user.id, preferences_update
    )
    return updated_preferences


@router.get("/me/tier-status", response_model=TierStatusRead)
async def get_tier_status(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get current user's tier status with stock count and limits"""
    tier_check = await check_tier_limit(session, user.id)
    
    return TierStatusRead(
        tier=user.tier,
        stock_count=tier_check.get('stock_count', 0),
        stock_limit=tier_check.get('limit'),
        can_add_more=tier_check.get('allowed', False),
    )


router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate))
