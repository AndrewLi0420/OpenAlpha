"""User preferences schemas"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.models.enums import HoldingPeriodEnum, RiskToleranceEnum


class UserPreferencesBase(BaseModel):
    """Base schema for user preferences"""
    holding_period: HoldingPeriodEnum = HoldingPeriodEnum.DAILY
    risk_tolerance: RiskToleranceEnum = RiskToleranceEnum.MEDIUM


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences"""
    user_id: UUID


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    holding_period: HoldingPeriodEnum | None = None
    risk_tolerance: RiskToleranceEnum | None = None


class UserPreferencesRead(UserPreferencesBase):
    """Schema for reading user preferences"""
    id: UUID
    user_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True
