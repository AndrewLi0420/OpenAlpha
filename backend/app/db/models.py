from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr

from app.db.config import Base


class TimeStampedModel(Base):
    """Base model with created_at and updated_at timestamps"""
    __abstract__ = True

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )
