"""Pytest configuration and fixtures"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.config import Base
# Ensure all models are imported so metadata includes every table
import app.models  # noqa: F401
from app.models.enums import TierEnum


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session"""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create all tables (drop first to avoid conflicts)
    async with engine.begin() as conn:
        # Drop all tables and indexes if they exist
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass  # Ignore errors if tables don't exist
        
        # Create tables and indexes
        # Use bind=conn to ensure we're using the same connection
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            # If create_all fails due to index conflicts, drop and recreate
            # This handles cases where indexes are defined both in __table_args__ and via index=True
            try:
                # Drop again to clear any partial state
                await conn.run_sync(Base.metadata.drop_all)
                # Recreate from scratch
                await conn.run_sync(Base.metadata.create_all)
            except Exception as e2:
                # Log but don't fail - some models may not be importable in test context
                import warnings
                warnings.warn(f"Could not create all tables: {e2}")

        # Ensure critical tables exist (work around index warnings interfering with create_all)
        def _ensure_tables_sync(sync_conn):
            for table_name in ("user_stock_tracking", "sentiment_data"):
                table = Base.metadata.tables.get(table_name)
                if table is not None:
                    table.create(bind=sync_conn, checkfirst=True)

        try:
            await conn.run_sync(_ensure_tables_sync)
        except Exception:
            pass
    
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Ensure the application uses this same test engine/session maker during tests
    try:
        import app.db.config as app_db_config  # type: ignore
        app_db_config.engine = engine
        app_db_config.async_session_maker = async_session_maker
    except Exception:
        pass
    
    async with async_session_maker() as session:
        yield session
        # Rollback any pending transactions
        await session.rollback()
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user_data():
    """Test user data fixture"""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",  # Must meet complexity requirements: 8+ chars, numbers/special chars
        "tier": TierEnum.FREE,
    }

