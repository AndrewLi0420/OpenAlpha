"""Unit tests for user registration functionality"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi_users.exceptions import InvalidPasswordException
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.users.manager import UserManager
from app.users.models import User
from app.models.enums import TierEnum


@pytest.fixture
def user_manager():
    """Create a UserManager instance for testing"""
    from unittest.mock import AsyncMock
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    mock_user_db = AsyncMock(spec=SQLAlchemyUserDatabase)
    return UserManager(mock_user_db)


@pytest.mark.asyncio
async def test_password_validation_minimum_length(user_manager):
    """Test password validation: minimum 8 characters enforced (AC 3)"""
    # Create a temporary user object for validation
    test_user = User(email="test@example.com")
    
    # Password too short should raise exception
    with pytest.raises(InvalidPasswordException) as exc_info:
        await user_manager.validate_password("short", test_user)
    assert "at least 8 characters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_password_validation_complexity_alpha_only(user_manager):
    """Test password validation: complexity check - alpha only fails (AC 3)"""
    test_user = User(email="test@example.com")
    
    # Password with only letters should raise exception
    with pytest.raises(InvalidPasswordException) as exc_info:
        await user_manager.validate_password("passwordonlyletters", test_user)
    assert "number or special characters" in str(exc_info.value)


@pytest.mark.asyncio
async def test_password_validation_complexity_numeric_only(user_manager):
    """Test password validation: complexity check - numeric only fails (AC 3)"""
    test_user = User(email="test@example.com")
    
    # Password with only numbers should raise exception
    with pytest.raises(InvalidPasswordException) as exc_info:
        await user_manager.validate_password("12345678", test_user)
    assert "only numeric values" in str(exc_info.value)


@pytest.mark.asyncio
async def test_password_validation_contains_email(user_manager):
    """Test password validation: password should not contain email (AC 3)"""
    test_user = User(email="test@example.com")
    
    # Password containing email should raise exception
    with pytest.raises(InvalidPasswordException) as exc_info:
        await user_manager.validate_password("test@example.com123!", test_user)
    assert "contain e-mail" in str(exc_info.value)


@pytest.mark.asyncio
async def test_password_validation_valid_password(user_manager):
    """Test password validation: valid password passes (AC 3)"""
    test_user = User(email="test@example.com")
    
    # Valid password should not raise exception
    try:
        await user_manager.validate_password("ValidPass123!", test_user)
    except InvalidPasswordException:
        pytest.fail("Valid password should not raise InvalidPasswordException")


def test_email_validation_format():
    """Test email validation: valid formats pass, invalid formats rejected (AC 2)
    Note: This test doesn't require database session - it's just testing Pydantic EmailStr validation
    """
    from pydantic import ValidationError, BaseModel
    from pydantic import field_validator
    
    # Use a Pydantic model to test EmailStr validation
    class EmailModel(BaseModel):
        email: str  # Using EmailStr annotation
        
        @field_validator('email')
        @classmethod
        def validate_email_format(cls, v: str) -> str:
            from pydantic import EmailStr
            import email_validator
            try:
                # Validate email format using email-validator (which EmailStr uses)
                email_validator.validate_email(v, check_deliverability=False)
                return v
            except email_validator.EmailNotValidError:
                raise ValueError("Invalid email format")
    
    # Valid email formats should pass
    valid_emails = [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.co.uk",
    ]
    
    for email in valid_emails:
        try:
            # EmailStr validates format via model
            model = EmailModel(email=email)
            assert model.email == email
        except ValidationError:
            pytest.fail(f"Valid email {email} should not raise ValidationError")
    
    # Invalid email formats should fail
    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user@.com",
    ]
    
    for email in invalid_emails:
        with pytest.raises(ValidationError):
            EmailModel(email=email)


@pytest.mark.asyncio
async def test_password_hashing_via_user_manager(db_session):
    """Test password hashing: verify password_hash is different from input, bcrypt verification works (AC 4)"""
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    from app.users.manager import UserManager
    from app.users.schemas import UserCreate
    
    plain_password = "SecurePass123!"
    user_create = UserCreate(email="hash_test@example.com", password=plain_password)
    
    # Create user via UserManager (which handles password hashing)
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = UserManager(user_db)
    
    # Mock queue.enqueue to avoid async cleanup issues in tests
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        created_user = await user_manager.create(user_create)
    
    # Commit session to ensure user is persisted
    await db_session.commit()
    await db_session.refresh(created_user)
    
    # Verify hash is different from plain password
    # FastAPI Users uses 'hashed_password' field name
    assert created_user.hashed_password != plain_password
    assert len(created_user.hashed_password) > len(plain_password)
    
    # Verify bcrypt verification works (via UserManager password helper)
    # FastAPI Users password_helper uses 'verify_and_update' which returns (bool, str | None)
    verified, _ = user_manager.password_helper.verify_and_update(plain_password, created_user.hashed_password)
    assert verified is True
    
    # Verify wrong password fails
    verified_wrong, _ = user_manager.password_helper.verify_and_update("WrongPassword", created_user.hashed_password)
    assert verified_wrong is False


@pytest.mark.asyncio
async def test_user_creation_defaults(db_session, test_user_data):
    """Test user creation: verify user created with tier='free', is_verified=False (AC 1, 4)"""
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    from app.users.manager import UserManager
    from app.users.schemas import UserCreate
    
    user_create = UserCreate(
        email=test_user_data["email"],
        password=test_user_data["password"],
    )
    
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = UserManager(user_db)
    
    # Mock queue.enqueue to avoid async cleanup issues in tests
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        created_user = await user_manager.create(user_create)
    
    # Commit session to ensure user is persisted
    await db_session.commit()
    await db_session.refresh(created_user)
    
    # Verify defaults
    assert created_user.email == test_user_data["email"]
    assert created_user.tier == TierEnum.FREE
    assert created_user.is_verified is False
    assert created_user.id is not None

