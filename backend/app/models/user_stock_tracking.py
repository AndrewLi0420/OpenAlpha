"""User stock tracking model for tier enforcement"""
from __future__ import annotations

from uuid import UUID, uuid4
from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.config import Base
from app.db.models import TimeStampedModel


class UserStockTracking(TimeStampedModel):
    """Tracks which stocks a user follows (enforces 5-stock limit for free tier)"""
    __tablename__ = "user_stock_tracking"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stock_id = Column(PG_UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="tracked_stocks")
    stock = relationship("Stock", back_populates="tracked_by_users")

    __table_args__ = (
        Index('ix_user_stock_tracking_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<UserStockTracking(user_id={self.user_id}, stock_id={self.stock_id})>"

