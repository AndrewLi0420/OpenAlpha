"""Pydantic schemas for ML inference service"""
from __future__ import annotations

from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field


class MarketDataInput(BaseModel):
    """Market data input for ML inference"""
    price: float = Field(..., gt=0, description="Stock price")
    volume: int = Field(..., gt=0, description="Trading volume")


class MLPredictRequest(BaseModel):
    """Request schema for ML prediction endpoint"""
    stock_id: UUID = Field(..., description="UUID of the stock")
    market_data: MarketDataInput | None = Field(
        None,
        description="Optional market data (price, volume). If not provided, will be loaded from database."
    )
    sentiment_score: float | None = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Optional sentiment score [-1, 1]. If not provided, will be loaded from database."
    )
    use_ensemble: bool = Field(
        True,
        description="Whether to use ensemble prediction (combine neural network and Random Forest)"
    )


class ModelPrediction(BaseModel):
    """Individual model prediction details"""
    signal: Literal["buy", "sell", "hold"] = Field(..., description="Prediction signal")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    class_: int = Field(..., alias="class", description="Predicted class (0=hold, 1=buy, 2=sell)")
    probabilities: list[float] = Field(..., description="Class probabilities")


class MLPredictResponse(BaseModel):
    """Response schema for ML prediction endpoint"""
    signal: Literal["buy", "sell", "hold"] = Field(..., description="Final prediction signal")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0, 1]")
    model_used: Literal["neural_network", "random_forest", "ensemble"] = Field(
        ...,
        description="Model(s) used for prediction"
    )
    latency_ms: float = Field(..., ge=0, description="Inference latency in milliseconds")
    neural_network_prediction: ModelPrediction | None = Field(
        None,
        description="Neural network prediction details (if available)"
    )
    random_forest_prediction: ModelPrediction | None = Field(
        None,
        description="Random Forest prediction details (if available)"
    )

