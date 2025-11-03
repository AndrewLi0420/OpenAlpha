import uuid
from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)

from app.users.manager import get_user_manager
from app.users.models import User
from app.users.schemas import UserCreate, UserRead
from .config import settings, Environment

# Configure CookieTransport with HTTP-only cookies
# Cookie settings: httpOnly=True, secure=True (production only), sameSite='lax'
cookie_transport = CookieTransport(
    cookie_name="fastapi-users:auth",
    cookie_max_age=settings.AUTH_TOKEN_LIFETIME_SECONDS,
    cookie_httponly=True,
    cookie_secure=settings.ENVIRONMENT == Environment.prod,
    cookie_samesite="lax",
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.AUTH_TOKEN_LIFETIME_SECONDS,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])




def get_auth_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    router.include_router(fastapi_users.get_auth_router(auth_backend))
    router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))
    router.include_router(fastapi_users.get_reset_password_router())
    router.include_router(fastapi_users.get_verify_router(UserRead))
    return router


current_user = fastapi_users.current_user(active=True)
superuser = fastapi_users.current_user(active=True, superuser=True)
