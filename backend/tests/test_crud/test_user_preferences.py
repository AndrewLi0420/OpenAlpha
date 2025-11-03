"""Unit tests for user preferences CRUD functions"""
import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy import select, func

from app.crud.users import get_user_preferences, upsert_user_preferences
from app.models.user_preferences import UserPreferences
from app.models.enums import HoldingPeriodEnum, RiskToleranceEnum
from app.schemas.user_preferences import UserPreferencesUpdate
from app.users.models import User
from app.models.enums import TierEnum


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="$2b$12$dummyhash",  # Dummy bcrypt hash for testing
        tier=TierEnum.FREE,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_user_preferences_existing(db_session, test_user):
    """Test get_user_preferences returns preferences for existing user"""
    # Create preferences for user
    preferences = UserPreferences(
        id=uuid4(),
        user_id=test_user.id,
        holding_period=HoldingPeriodEnum.WEEKLY,
        risk_tolerance=RiskToleranceEnum.HIGH,
    )
    db_session.add(preferences)
    await db_session.commit()

    # Get preferences
    result = await get_user_preferences(db_session, test_user.id)

    assert result is not None
    assert result.user_id == test_user.id
    assert result.holding_period == HoldingPeriodEnum.WEEKLY
    assert result.risk_tolerance == RiskToleranceEnum.HIGH


@pytest.mark.asyncio
async def test_get_user_preferences_nonexistent(db_session, test_user):
    """Test get_user_preferences returns None for user without preferences"""
    result = await get_user_preferences(db_session, test_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_upsert_user_preferences_create(db_session, test_user):
    """Test upsert_user_preferences creates new preferences"""
    update_data = UserPreferencesUpdate(
        holding_period=HoldingPeriodEnum.MONTHLY,
        risk_tolerance=RiskToleranceEnum.LOW,
    )

    result = await upsert_user_preferences(db_session, test_user.id, update_data)

    assert result is not None
    assert result.user_id == test_user.id
    assert result.holding_period == HoldingPeriodEnum.MONTHLY
    assert result.risk_tolerance == RiskToleranceEnum.LOW

    # Verify preferences were saved to database
    db_prefs = await get_user_preferences(db_session, test_user.id)
    assert db_prefs is not None
    assert db_prefs.holding_period == HoldingPeriodEnum.MONTHLY
    assert db_prefs.risk_tolerance == RiskToleranceEnum.LOW


@pytest.mark.asyncio
async def test_upsert_user_preferences_update(db_session, test_user):
    """Test upsert_user_preferences updates existing preferences"""
    # Create initial preferences
    initial_prefs = UserPreferences(
        id=uuid4(),
        user_id=test_user.id,
        holding_period=HoldingPeriodEnum.DAILY,
        risk_tolerance=RiskToleranceEnum.MEDIUM,
    )
    db_session.add(initial_prefs)
    await db_session.commit()
    initial_id = initial_prefs.id

    # Update preferences
    update_data = UserPreferencesUpdate(
        holding_period=HoldingPeriodEnum.WEEKLY,
        risk_tolerance=RiskToleranceEnum.HIGH,
    )

    result = await upsert_user_preferences(db_session, test_user.id, update_data)

    assert result is not None
    assert result.id == initial_id  # Same record updated
    assert result.holding_period == HoldingPeriodEnum.WEEKLY
    assert result.risk_tolerance == RiskToleranceEnum.HIGH

    # Verify only one preferences record exists (check by querying again)
    count_result = await db_session.execute(
        select(func.count(UserPreferences.id)).where(
            UserPreferences.user_id == test_user.id
        )
    )
    count = count_result.scalar()
    assert count == 1
    assert result.user_id == test_user.id


@pytest.mark.asyncio
async def test_upsert_user_preferences_partial_update(db_session, test_user):
    """Test upsert_user_preferences updates only provided fields"""
    # Create initial preferences
    initial_prefs = UserPreferences(
        id=uuid4(),
        user_id=test_user.id,
        holding_period=HoldingPeriodEnum.DAILY,
        risk_tolerance=RiskToleranceEnum.MEDIUM,
    )
    db_session.add(initial_prefs)
    await db_session.commit()

    # Update only holding_period
    update_data = UserPreferencesUpdate(holding_period=HoldingPeriodEnum.MONTHLY)

    result = await upsert_user_preferences(db_session, test_user.id, update_data)

    assert result.holding_period == HoldingPeriodEnum.MONTHLY
    assert result.risk_tolerance == RiskToleranceEnum.MEDIUM  # Unchanged


@pytest.mark.asyncio
async def test_upsert_user_preferences_defaults_on_create(db_session, test_user):
    """Test upsert_user_preferences uses defaults when creating without values"""
    update_data = UserPreferencesUpdate()  # No values provided

    result = await upsert_user_preferences(db_session, test_user.id, update_data)

    assert result is not None
    assert result.holding_period == HoldingPeriodEnum.DAILY  # Default
    assert result.risk_tolerance == RiskToleranceEnum.MEDIUM  # Default

