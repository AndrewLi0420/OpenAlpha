"""Recommendations API endpoints"""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.config import get_db
from app.services.recommendation_service import generate_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate(
    user_id: UUID = Query(..., description="Target user UUID for generation"),
    count: int = Query(10, ge=1, le=100, description="Number of recommendations to generate"),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Trigger recommendation generation on-demand.

    Returns minimal summary (count created). Intended for admin/internal use.
    """
    try:
        recs = await generate_recommendations(
            session=session,
            user_id=user_id,
            daily_target_count=count,
            use_ensemble=True,
        )
        return {"created": len(recs)}
    except Exception as e:
        logger.error("Generation endpoint failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Generation failed")


