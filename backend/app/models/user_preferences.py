"""User preferences model"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, ForeignKey, Enum as SQLEnum, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.config import Base
from app.models.enums import HoldingPeriodEnum, RiskToleranceEnum


class UserPreferences(Base):
    """User preferences model with 1:1 relationship to User"""
    __tablename__ = "user_preferences"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    holding_period = Column(
        SQLEnum(HoldingPeriodEnum, native_enum=False),
        default=HoldingPeriodEnum.DAILY,
        nullable=False
    )
    risk_tolerance = Column(
        SQLEnum(RiskToleranceEnum, native_enum=False),
        default=RiskToleranceEnum.MEDIUM,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship
    user = relationship("User", back_populates="preferences", uselist=False)

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_preferences_user_id'),
    )

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, holding_period={self.holding_period}, risk_tolerance={self.risk_tolerance})>"
