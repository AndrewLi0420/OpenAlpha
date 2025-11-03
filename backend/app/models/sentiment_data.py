"""Sentiment data model"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, ForeignKey, Numeric, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.config import Base


class SentimentData(Base):
    """Sentiment data time-series model for multi-source aggregation"""
    __tablename__ = "sentiment_data"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    stock_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sentiment_score = Column(Numeric(precision=5, scale=4), nullable=False)  # Normalized -1 to 1 or 0 to 1
    source = Column(String(255), nullable=False)  # e.g., 'twitter', 'news'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    stock = relationship("Stock", back_populates="sentiment_data")

    __table_args__ = (
        Index('ix_sentiment_data_stock_id', 'stock_id'),
        Index('ix_sentiment_data_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<SentimentData(stock_id={self.stock_id}, sentiment_score={self.sentiment_score}, source={self.source}, timestamp={self.timestamp})>"
