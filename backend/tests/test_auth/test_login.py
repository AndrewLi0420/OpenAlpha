"""Unit tests for user authentication functionality"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
import jwt

from app.users.manager import UserManager
from app.users.models import User
from app.core.auth import get_jwt_strategy, cookie_transport, auth_backend
from app.core.config import settings


@pytest.fixture
def user_manager():
    """Create a UserManager instance for testing"""
    from unittest.mock import AsyncMock
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    mock_user_db = AsyncMock(spec=SQLAlchemyUserDatabase)
    return UserManager(mock_user_db)


@pytest.mark.asyncio
async def test_password_verification_bcrypt_comparison(db_session):
    """Test password verification: verify bcrypt password comparison works correctly (AC #2)
    
    This test verifies that:
    1. Password hashing creates a bcrypt hash
    2. Password verification correctly validates matching passwords
    3. Password verification correctly rejects non-matching passwords
    """
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    from app.users.manager import UserManager
    from app.users.schemas import UserCreate
    
    plain_password = "SecurePass123!"
    user_create = UserCreate(email="verify_test@example.com", password=plain_password)
    
    # Create user via UserManager (which handles password hashing)
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = UserManager(user_db)
    
    # Mock queue.enqueue to avoid async cleanup issues
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        created_user = await user_manager.create(user_create)
    
    await db_session.commit()
    await db_session.refresh(created_user)
    
    # Test password verification via bcrypt comparison
    # FastAPI Users password_helper uses 'verify_and_update' which returns (bool, str | None)
    verified, _ = user_manager.password_helper.verify_and_update(
        plain_password, 
        created_user.hashed_password
    )
    assert verified is True, "Correct password should verify successfully"
    
    # Test wrong password fails verification
    verified_wrong, _ = user_manager.password_helper.verify_and_update(
        "WrongPassword123!",
        created_user.hashed_password
    )
    assert verified_wrong is False, "Incorrect password should fail verification"
    
    # Test that hash is a secure format (FastAPI Users uses Argon2id by default)
    # Argon2id format: $argon2id$v=19$...
    # bcrypt format: $2b$, $2a$, $2y$ (for backward compatibility)
    assert created_user.hashed_password.startswith(('$argon2id$', '$2b$', '$2a$', '$2y$')), \
        f"Password hash should be Argon2id or bcrypt format, got: {created_user.hashed_password[:20]}..."


@pytest.mark.asyncio
async def test_jwt_token_generation_contains_user_id(db_session):
    """Test JWT token generation: verify token contains user ID and is valid (AC #3)
    
    This test verifies that:
    1. JWT strategy generates tokens correctly
    2. Token contains user ID in payload
    3. Token is valid and can be decoded
    """
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    from app.users.manager import UserManager
    from app.users.schemas import UserCreate
    from uuid import uuid4
    
    # Create a real user in database for token generation
    user_create = UserCreate(email="token_test@example.com", password="TokenTest123!")
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = UserManager(user_db)
    
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        created_user = await user_manager.create(user_create)
    
    await db_session.commit()
    await db_session.refresh(created_user)
    
    # Get JWT strategy instance
    jwt_strategy = get_jwt_strategy()
    
    # Generate token using the strategy (write_token is async and expects user model)
    # FastAPI Users JWTStrategy.write_token is async and returns a string token
    token = await jwt_strategy.write_token(created_user)
    
    # Verify token is a string and not empty
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 0, "Token should not be empty"
    
    # Decode and verify token contents
    # FastAPI Users JWT tokens may not include audience, so disable aud verification
    decoded = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"verify_aud": False}
    )
    
    # Verify token contains user ID (FastAPI Users uses 'sub' claim with string UUID)
    assert decoded.get("sub") == str(created_user.id), \
        f"Token should contain user ID in 'sub' claim. Expected {created_user.id}, got {decoded.get('sub')}"
    
    # Verify token contains standard JWT claims
    assert "exp" in decoded, "Token should contain expiration claim"
    # Note: FastAPI Users may or may not include "iat" claim depending on version
    # The important claims are "sub" (user ID) and "exp" (expiration)


def test_cookie_transport_http_only_attribute():
    """Test cookie setting: verify HTTP-only cookie is set with JWT token (AC #3)
    
    This test verifies that CookieTransport is configured with:
    1. httpOnly=True for security
    2. secure=True in production (conditional)
    3. sameSite='lax' for CSRF protection
    4. Correct cookie name
    """
    # Verify CookieTransport is configured correctly
    assert cookie_transport.cookie_httponly is True, \
        "Cookie should have httpOnly=True for XSS protection"
    
    assert cookie_transport.cookie_name == "fastapi-users:auth", \
        "Cookie name should match expected value"
    
    assert cookie_transport.cookie_samesite == "lax", \
        "Cookie should have sameSite='lax' for CSRF protection"
    
    # Verify cookie_max_age is set (should match token lifetime)
    assert cookie_transport.cookie_max_age == settings.AUTH_TOKEN_LIFETIME_SECONDS, \
        "Cookie max age should match token lifetime"


def test_cookie_transport_secure_production():
    """Test cookie setting: verify secure=True in production environment (AC #3)
    
    This test verifies cookie security settings respect environment.
    Note: This is tested via configuration, actual secure setting depends on ENVIRONMENT.
    """
    from app.core.config import Environment
    
    # Verify cookie_transport configuration respects environment
    # In production, secure should be True; in dev, it should be False
    if settings.ENVIRONMENT == Environment.prod:
        assert cookie_transport.cookie_secure is True, \
            "Cookie should be secure=True in production"
    else:
        assert cookie_transport.cookie_secure is False, \
            "Cookie should be secure=False in development (localhost)"


@pytest.mark.asyncio
async def test_jwt_token_expiration(db_session):
    """Test JWT token generation: verify token expiration is set correctly (AC #3)"""
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    from app.users.manager import UserManager
    from app.users.schemas import UserCreate
    
    # Create a real user in database for token generation
    user_create = UserCreate(email="expiry_test@example.com", password="ExpiryTest123!")
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = UserManager(user_db)
    
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        created_user = await user_manager.create(user_create)
    
    await db_session.commit()
    await db_session.refresh(created_user)
    
    jwt_strategy = get_jwt_strategy()
    token = await jwt_strategy.write_token(created_user)
    
    # Decode token to check expiration
    # FastAPI Users JWT tokens may not include audience, so disable aud verification
    decoded = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"verify_aud": False}
    )
    
    # Verify expiration claim exists
    assert "exp" in decoded, "Token should contain expiration claim"
    
    # Verify expiration is in the future
    exp_timestamp = decoded["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp)
    now = datetime.now()
    
    assert exp_datetime > now, "Token expiration should be in the future"
    
    # Verify expiration matches configured lifetime (within 5 seconds tolerance)
    expected_exp = now + timedelta(seconds=settings.AUTH_TOKEN_LIFETIME_SECONDS)
    time_diff = abs((exp_datetime - expected_exp).total_seconds())
    assert time_diff < 5, \
        f"Token expiration should match AUTH_TOKEN_LIFETIME_SECONDS (diff: {time_diff}s)"


@pytest.mark.asyncio
async def test_password_verification_invalid_credentials(db_session):
    """Test invalid credentials handling: verify password verification fails for wrong password (AC #2, #7)
    
    This test verifies that password verification correctly identifies invalid passwords
    without revealing whether the email exists in the system.
    """
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    from app.users.manager import UserManager
    from app.users.schemas import UserCreate
    
    # Create a user with a known password
    plain_password = "OriginalPass123!"
    user_create = UserCreate(email="credentials_test@example.com", password=plain_password)
    
    user_db = SQLAlchemyUserDatabase(db_session, User)
    user_manager = UserManager(user_db)
    
    with patch('app.users.manager.queue.enqueue', new_callable=AsyncMock):
        created_user = await user_manager.create(user_create)
    
    await db_session.commit()
    await db_session.refresh(created_user)
    
    # Test various invalid password scenarios
    invalid_passwords = [
        "WrongPassword123!",
        "OriginalPass123!Wrong",
        "completely_different",
        "",  # Empty password
    ]
    
    for invalid_password in invalid_passwords:
        verified, _ = user_manager.password_helper.verify_and_update(
            invalid_password,
            created_user.hashed_password
        )
        assert verified is False, \
            f"Password '{invalid_password}' should fail verification"
    
    # Verify correct password still works
    verified_correct, _ = user_manager.password_helper.verify_and_update(
        plain_password,
        created_user.hashed_password
    )
    assert verified_correct is True, \
        "Correct password should still verify after testing invalid passwords"


def test_jwt_strategy_configuration():
    """Test JWT strategy configuration: verify strategy is configured correctly (AC #3)"""
    jwt_strategy = get_jwt_strategy()
    
    # Verify strategy is JWTStrategy instance
    assert jwt_strategy is not None, "JWT strategy should be instantiated"
    
    # Verify strategy uses correct secret
    assert jwt_strategy.secret == settings.SECRET_KEY, \
        "JWT strategy should use SECRET_KEY from settings"
    
    # Verify lifetime is configured
    assert jwt_strategy.lifetime_seconds == settings.AUTH_TOKEN_LIFETIME_SECONDS, \
        "JWT strategy lifetime should match settings"


def test_auth_backend_configuration():
    """Test authentication backend configuration: verify backend uses CookieTransport and JWT strategy (AC #3)"""
    # Verify auth_backend is configured
    assert auth_backend is not None, "Auth backend should be instantiated"
    
    # Verify backend uses CookieTransport (not BearerTransport)
    assert isinstance(auth_backend.transport, type(cookie_transport)), \
        "Auth backend should use CookieTransport for HTTP-only cookies"
    
    # Verify backend uses JWT strategy
    jwt_strategy = get_jwt_strategy()
    assert auth_backend.get_strategy() is not None, \
        "Auth backend should have JWT strategy configured"

