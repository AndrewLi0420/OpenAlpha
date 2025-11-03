"""Enum types for database models"""
import enum


class TierEnum(str, enum.Enum):
    """User subscription tier"""
    FREE = "free"
    PREMIUM = "premium"


class HoldingPeriodEnum(str, enum.Enum):
    """User preference for holding period"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RiskToleranceEnum(str, enum.Enum):
    """User risk tolerance level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SignalEnum(str, enum.Enum):
    """Recommendation signal"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class RiskLevelEnum(str, enum.Enum):
    """Risk level for recommendation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
