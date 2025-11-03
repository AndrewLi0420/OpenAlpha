from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URI).replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def register_db(app) -> None:
    """Register database shutdown on app shutdown"""
    @app.on_event("shutdown")
    async def shutdown_db():
        await engine.dispose()
