"""Sentiment data schemas"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class SentimentDataBase(BaseModel):
    """Base schema for sentiment data"""
    stock_id: UUID
    sentiment_score: float  # Normalized -1 to 1 or 0 to 1
    source: str
    timestamp: datetime


class SentimentDataCreate(SentimentDataBase):
    """Schema for creating sentiment data"""
    pass


class SentimentDataUpdate(BaseModel):
    """Schema for updating sentiment data"""
    sentiment_score: float | None = None
    source: str | None = None
    timestamp: datetime | None = None


class SentimentDataRead(SentimentDataBase):
    """Schema for reading sentiment data"""
    id: UUID

    class Config:
        from_attributes = True
