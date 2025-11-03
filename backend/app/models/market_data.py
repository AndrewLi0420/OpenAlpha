"""Market data model"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, ForeignKey, Numeric, BigInteger, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.config import Base


class MarketData(Base):
    """Market data time-series model"""
    __tablename__ = "market_data"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    stock_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    price = Column(Numeric(precision=10, scale=2), nullable=False)
    volume = Column(BigInteger, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    stock = relationship("Stock", back_populates="market_data")

    __table_args__ = (
        Index('ix_market_data_stock_id', 'stock_id'),
        Index('ix_market_data_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<MarketData(stock_id={self.stock_id}, price={self.price}, timestamp={self.timestamp})>"
