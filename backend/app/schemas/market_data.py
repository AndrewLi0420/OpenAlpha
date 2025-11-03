"""Market data schemas"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class MarketDataBase(BaseModel):
    """Base schema for market data"""
    stock_id: UUID
    price: float
    volume: int
    timestamp: datetime


class MarketDataCreate(MarketDataBase):
    """Schema for creating market data"""
    pass


class MarketDataUpdate(BaseModel):
    """Schema for updating market data"""
    price: float | None = None
    volume: int | None = None
    timestamp: datetime | None = None


class MarketDataRead(MarketDataBase):
    """Schema for reading market data"""
    id: UUID

    class Config:
        from_attributes = True
