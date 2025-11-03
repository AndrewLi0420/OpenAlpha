from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.db.config import get_db
from app.db.config import async_session_maker

router = APIRouter(prefix="/api/v1/health")


class APIHealth(BaseModel):
    database_is_online: bool = True


@router.get(
    "/",
    response_model=APIHealth,
    responses={
        503: {"description": "Services are unavailable", "model": APIHealth}
    },
)
async def check_health(response: Response):
    """Check availability of API health."""
    logger.info("Health Check⛑")
    
    # Check database connection
    database_is_online = False
    try:
        async with async_session_maker() as session:
            # Simple query to test database connection
            result = await session.execute(select(text("1")))
            result.scalar()
            database_is_online = True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        database_is_online = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    health = APIHealth(database_is_online=database_is_online)
    return health
