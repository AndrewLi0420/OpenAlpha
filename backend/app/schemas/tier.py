"""Schemas for tier status endpoints"""
from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import TierEnum


class TierStatusRead(BaseModel):
    """Tier status response"""
    tier: TierEnum
    stock_count: int
    stock_limit: int | None
    can_add_more: bool

    class Config:
        from_attributes = True

