"""Stock schemas"""
from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel


class StockBase(BaseModel):
    """Base schema for stock"""
    symbol: str
    company_name: str
    sector: str | None = None
    fortune_500_rank: int | None = None


class StockCreate(StockBase):
    """Schema for creating stock"""
    pass


class StockUpdate(BaseModel):
    """Schema for updating stock"""
    company_name: str | None = None
    sector: str | None = None
    fortune_500_rank: int | None = None


class StockRead(StockBase):
    """Schema for reading stock"""
    id: UUID

    class Config:
        from_attributes = True
