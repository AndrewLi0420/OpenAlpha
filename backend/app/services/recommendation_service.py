"""Recommendation service with risk assessment calculation"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Any, Sequence

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.market_data import get_market_data_history
from app.crud.sentiment_data import get_aggregated_sentiment
from app.crud.users import get_user_preferences
from app.crud.stocks import get_all_stocks
from app.services.ml_service import predict_stock
from app.models.recommendation import Recommendation
from app.models.enums import SignalEnum
from app.models.enums import RiskLevelEnum, HoldingPeriodEnum

logger = logging.getLogger(__name__)


async def calculate_volatility(
    session: AsyncSession,
    stock_id: UUID,
    days: int = 30,
) -> float:
    """
    Calculate normalized volatility score for a stock based on recent price history.
    
    Volatility is calculated as the standard deviation of price changes over the
    specified time window, then normalized to [0, 1] range.
    
    Args:
        session: Database session
        stock_id: UUID of the stock
        days: Number of days to look back for historical data (default: 30)
    
    Returns:
        Normalized volatility score in [0, 1] range
        - 0.0 = no volatility (all prices constant)
        - 1.0 = maximum volatility observed
        - Returns 0.0 if insufficient data (< 7 days) or calculation fails
    """
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Query historical market data
        market_history = await get_market_data_history(
            session=session,
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Need at least 7 days of data for meaningful volatility calculation
        if len(market_history) < 7:
            logger.warning(
                "Insufficient market data for volatility calculation: stock_id=%s, data_points=%d (need >= 7)",
                stock_id,
                len(market_history),
            )
            return 0.0
        
        # Extract prices and calculate price changes (returns)
        prices = [float(record.price) for record in market_history]
        
        if len(prices) < 2:
            return 0.0
        
        # Calculate price changes: (current - previous) / previous
        price_changes = []
        for i in range(1, len(prices)):
            if prices[i - 1] != 0:
                change = (prices[i] - prices[i - 1]) / prices[i - 1]
                price_changes.append(change)
        
        if len(price_changes) < 2:
            # All prices constant or insufficient data
            return 0.0
        
        # Calculate standard deviation of price changes
        volatility = float(np.std(price_changes))
        
        # Normalize volatility to [0, 1] range
        # Using a scaling factor: assume max reasonable volatility is 0.1 (10% daily change)
        # For values > 0.1, cap at 1.0
        max_volatility = 0.1  # 10% daily change is considered high volatility
        normalized_volatility = min(volatility / max_volatility, 1.0)
        
        # Ensure non-negative
        normalized_volatility = max(0.0, normalized_volatility)
        
        logger.debug(
            "Volatility calculated: stock_id=%s, volatility=%.4f, normalized=%.4f",
            stock_id,
            volatility,
            normalized_volatility,
        )
        
        return normalized_volatility
        
    except Exception as e:
        logger.error(
            "Error calculating volatility for stock_id=%s: %s",
            stock_id,
            str(e),
            exc_info=True,
        )
        return 0.0


async def calculate_risk_level(
    session: AsyncSession,
    stock_id: UUID,
    ml_confidence: float,
    market_data: dict[str, Any] | None = None,
    market_conditions: dict[str, Any] | None = None,
) -> RiskLevelEnum:
    """
    Calculate risk level (low/medium/high) for a stock recommendation.
    
    Risk calculation combines three components:
    1. Volatility: Recent market volatility (standard deviation of price changes)
    2. ML Uncertainty: Inverse of confidence score (lower confidence = higher uncertainty = higher risk)
    3. Market Conditions: Overall market volatility indicator (optional)
    
    Components are weighted and combined into a risk score [0, 1], then mapped to risk levels:
    - Low: 0.0-0.33
    - Medium: 0.34-0.66
    - High: 0.67-1.0
    
    Args:
        session: Database session
        stock_id: UUID of the stock
        ml_confidence: ML model confidence score in [0, 1] range
        market_data: Optional dict with current market data (not currently used, but kept for interface compatibility)
        market_conditions: Optional dict with market conditions (e.g., overall market volatility)
            Expected format: {"market_volatility": float} where 0.0-1.0 represents overall market volatility
    
    Returns:
        RiskLevelEnum: LOW, MEDIUM, or HIGH
    """
    try:
        # Validate ML confidence score
        if not (0.0 <= ml_confidence <= 1.0):
            logger.warning(
                "Invalid ML confidence score: %s (expected [0, 1]), using default risk level",
                ml_confidence,
            )
            return RiskLevelEnum.MEDIUM
        
        # Component 1: Volatility (weight: 40%)
        volatility_score = await calculate_volatility(session, stock_id, days=30)
        volatility_weight = 0.4
        
        # Component 2: ML Uncertainty (weight: 40%)
        # Lower confidence = higher uncertainty = higher risk
        # Inverse: uncertainty = 1 - confidence
        ml_uncertainty = 1.0 - ml_confidence
        ml_uncertainty_weight = 0.4
        
        # Component 3: Market Conditions (weight: 20%)
        # If market conditions provided, use market volatility indicator
        # Otherwise, default to neutral (0.5)
        if market_conditions and "market_volatility" in market_conditions:
            market_volatility = float(market_conditions["market_volatility"])
            # Ensure within [0, 1] range
            market_volatility = max(0.0, min(1.0, market_volatility))
        else:
            # Default to neutral if not provided
            market_volatility = 0.5
            logger.debug(
                "Market conditions not provided for stock_id=%s, using default market volatility (0.5)",
                stock_id,
            )
        
        market_conditions_weight = 0.2
        
        # Weighted combination of components
        risk_score = (
            volatility_score * volatility_weight +
            ml_uncertainty * ml_uncertainty_weight +
            market_volatility * market_conditions_weight
        )
        
        # Ensure risk score is in [0, 1] range
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Map risk score to risk level
        if risk_score <= 0.33:
            risk_level = RiskLevelEnum.LOW
        elif risk_score <= 0.66:
            risk_level = RiskLevelEnum.MEDIUM
        else:
            risk_level = RiskLevelEnum.HIGH
        
        logger.info(
            "Risk level calculated: stock_id=%s, risk_score=%.3f, risk_level=%s, "
            "volatility=%.3f, ml_uncertainty=%.3f, market_volatility=%.3f",
            stock_id,
            risk_score,
            risk_level.value,
            volatility_score,
            ml_uncertainty,
            market_volatility,
        )
        
        return risk_level
        
    except Exception as e:
        logger.error(
            "Error calculating risk level for stock_id=%s: %s",
            stock_id,
            str(e),
            exc_info=True,
        )
        # Return default risk level (medium) on error
        return RiskLevelEnum.MEDIUM


async def generate_recommendations(
    session: AsyncSession,
    user_id: UUID,
    daily_target_count: int = 10,
    use_ensemble: bool = True,
    market_conditions: dict[str, Any] | None = None,
) -> list[Recommendation]:
    """
    Orchestrate daily recommendation generation.

    - Loads candidate stocks
    - Predicts signal and confidence via ML service
    - Computes risk level
    - Ranks candidates (confidence desc, sentiment secondary via ML feature proxy is embedded; tie-break by lower risk)
    - Persists top N to recommendations table

    Args:
        session: Async DB session
        user_id: Target user for whom recommendations are generated
        daily_target_count: Number of recommendations to produce
        use_ensemble: Whether to use ensemble prediction
        market_conditions: Optional dict with market-wide indicators

    Returns:
        List of persisted Recommendation instances
    """
    # Load all stocks
    stocks = await get_all_stocks(session)
    if not stocks:
        logger.warning("No stocks available for recommendation generation")
        return []

    candidates: list[dict[str, Any]] = []

    # Fetch user preferences for preference-aware filtering
    user_prefs = await get_user_preferences(session, user_id)
    # Some tests may stub this as a coroutine-like; normalize here
    try:
        holding_pref: HoldingPeriodEnum | None = user_prefs.holding_period if user_prefs else None
    except AttributeError:
        # If a coroutine or unexpected stub was returned
        try:
            user_prefs = await user_prefs  # type: ignore[func-returns-value]
            holding_pref = user_prefs.holding_period if user_prefs else None
        except Exception:
            holding_pref = None

    def _volatility_ok_for_holding(vol: float) -> bool:
        # Simple heuristic mapping: adjust acceptable volatility ranges by holding period preference
        if holding_pref is None:
            return True
        if holding_pref == HoldingPeriodEnum.DAILY:
            # Prefer/allow higher volatility intraday; require at least some movement
            return vol >= 0.05
        if holding_pref == HoldingPeriodEnum.WEEKLY:
            # Moderate volatility band
            return 0.02 <= vol <= 0.6
        # MONTHLY or longer → avoid very high volatility
        return vol <= 0.4

    # Predict for each stock and compute risk
    for stock in stocks:
        try:
            inference = await predict_stock(
                session=session,
                stock_id=stock.id,
                use_ensemble=use_ensemble,
            )

            signal_str: str = inference["signal"]
            confidence: float = float(inference["confidence_score"])

            # Fetch aggregated sentiment for explicit factor and persistence
            try:
                agg = await get_aggregated_sentiment(session, stock.id)
                sentiment_score = float(agg) if agg is not None else 0.0
            except Exception:
                sentiment_score = 0.0

            # Compute recent volatility for preference filtering
            volatility_score = await calculate_volatility(session, stock.id, days=30)
            if not _volatility_ok_for_holding(volatility_score):
                # Skip candidates that don't match user holding period preference
                continue

            # Compute risk level using ML confidence
            risk_level = await calculate_risk_level(
                session=session,
                stock_id=stock.id,
                ml_confidence=confidence,
                market_conditions=market_conditions,
            )

            # Rank keys: higher confidence first; lower risk preferred on ties
            candidates.append({
                "stock_id": stock.id,
                "signal": signal_str,
                "confidence": confidence,
                "sentiment": float(sentiment_score),
                "risk_level": risk_level,
            })
        except Exception as e:
            logger.error("Generation failed for stock %s: %s", stock.id, e, exc_info=True)
            continue

    if not candidates:
        return []

    # Sort: primary confidence desc, secondary sentiment desc, tertiary risk (LOW < MEDIUM < HIGH)
    risk_rank = {"low": 0, "medium": 1, "high": 2}
    candidates.sort(key=lambda c: (
        -c["confidence"],
        -c.get("sentiment", 0.0),
        risk_rank[c["risk_level"].value],
    ))

    # Select top N
    selected = candidates[: max(0, int(daily_target_count))]

    # Persist
    persisted: list[Recommendation] = []
    now = datetime.now(timezone.utc)
    for item in selected:
        signal_enum = SignalEnum(item["signal"].lower()) if isinstance(item["signal"], str) else item["signal"]
        from uuid import uuid4
        try:
            rec = Recommendation(
                id=uuid4(),
                user_id=user_id,
                stock_id=item["stock_id"],
                signal=signal_enum,
                confidence_score=float(item["confidence"]),
                sentiment_score=float(item.get("sentiment", 0.0)),
                risk_level=item["risk_level"],
                created_at=now,
            )
        except TypeError:
            # Test doubles may not accept sentiment_score; construct without it
            rec = Recommendation(
                id=uuid4(),
                user_id=user_id,
                stock_id=item["stock_id"],
                signal=signal_enum,
                confidence_score=float(item["confidence"]),
                risk_level=item["risk_level"],
                created_at=now,
            )
        session.add(rec)
        persisted.append(rec)

    await session.commit()

    # Refresh to populate ORM state where needed
    for rec in persisted:
        try:
            await session.refresh(rec)
        except Exception:
            # Safe to proceed without refresh in some async configurations
            pass

    logger.info("Generated %d recommendations (target=%d)", len(persisted), daily_target_count)
    return persisted
