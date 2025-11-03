from __future__ import annotations

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, synonym

from app.db.config import Base, async_session_maker
from app.db.models import TimeStampedModel
from app.models.enums import TierEnum


class User(SQLAlchemyBaseUserTableUUID, TimeStampedModel):
    """User model with SQLAlchemy and FastAPI Users"""
    __tablename__ = "users"

    short_name = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    tier = Column(SQLEnum(TierEnum, native_enum=False), default=TierEnum.FREE, nullable=False)

    # Backwards-compat alias for tests expecting `password_hash`
    # FastAPI Users base defines `hashed_password`; expose a synonym for test constructors
    password_hash = synonym("hashed_password")

    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    tracked_stocks = relationship("UserStockTracking", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return self.short_name or self.full_name or self.email


async def get_user_db():
    """Get database session for FastAPI Users"""
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
    
    async with async_session_maker() as session:
        yield SQLAlchemyUserDatabase(session, User)
