"""Scheduled tasks for recommendation generation"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.recommendation_service import generate_recommendations
from app.users.models import User
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def scheduled_generation(
    session: AsyncSession,
    user_id: UUID,
    daily_target_count: int = 10,
) -> int:
    """
    Scheduled entrypoint to generate recommendations.

    Returns number of recommendations created.
    """
    logger.info(
        "Starting scheduled recommendation generation at %s (target=%d)",
        datetime.now(timezone.utc).isoformat(),
        daily_target_count,
    )

    recs = await generate_recommendations(
        session=session,
        user_id=user_id,
        daily_target_count=daily_target_count,
        use_ensemble=True,
        market_conditions=None,
    )

    logger.info("Scheduled generation completed: %d recommendations", len(recs))
    return len(recs)


async def recommendations_job(daily_target_count: int = 10) -> None:
    """APScheduler job to generate recommendations for all users.

    - Creates isolated DB engine/session
    - Iterates all users
    - Enforces soft latency target (<60s) with logging
    """
    logger.info(
        "Starting recommendations job at %s (target per user=%d)",
        datetime.now(timezone.utc).isoformat(),
        daily_target_count,
    )

    start = time.time()
    engine = None
    try:
        engine = create_async_engine(str(settings.DATABASE_URI))
        async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session_maker() as session:
            # Fetch all users
            users = (await session.execute(select(User))).scalars().all()
            if not users:
                logger.warning("No users found; skipping recommendations job")
                return

            total_created = 0
            for u in users:
                try:
                    created = await scheduled_generation(
                        session=session,
                        user_id=u.id,
                        daily_target_count=daily_target_count,
                    )
                    total_created += created
                except Exception as e:
                    logger.error("Generation failed for user %s: %s", u.id, e, exc_info=True)

            duration = time.time() - start
            logger.info(
                "Recommendations job completed: total=%d in %.2fs",
                total_created,
                duration,
            )
            if duration > 60.0:
                logger.warning("Recommendations job exceeded latency target: %.2fs > 60s", duration)
    finally:
        if engine is not None:
            try:
                await engine.dispose()
            except Exception:
                pass

