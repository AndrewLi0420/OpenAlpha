"""ML inference API endpoints"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.config import get_db
from app.schemas.ml import MLPredictRequest, MLPredictResponse, ModelPrediction
from app.services.ml_service import predict_stock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])


@router.post("/predict", response_model=MLPredictResponse, status_code=status.HTTP_200_OK)
async def predict(
    request: MLPredictRequest,
    session: AsyncSession = Depends(get_db),
) -> MLPredictResponse:
    """
    Generate ML prediction for a stock.
    
    Uses trained neural network and Random Forest models to generate buy/sell/hold
    predictions with confidence scores. Supports ensemble prediction (combining both models)
    or using individual models.
    
    Args:
        request: Prediction request with stock_id and optional market_data/sentiment_score
        session: Database session
    
    Returns:
        MLPredictResponse with prediction signal, confidence score, and model details
    
    Raises:
        HTTPException: If stock not found, model not loaded, or inference fails
    """
    try:
        # Convert request to predict_stock() arguments
        market_data_dict = None
        if request.market_data:
            market_data_dict = {
                "price": request.market_data.price,
                "volume": request.market_data.volume,
            }
        
        # Call inference service
        result = await predict_stock(
            session=session,
            stock_id=request.stock_id,
            market_data=market_data_dict,
            sentiment_score=request.sentiment_score,
            use_ensemble=request.use_ensemble,
        )
        
        # Convert to response schema
        # Convert nested predictions if present
        nn_pred = None
        if result.get("neural_network_prediction"):
            nn_data = result["neural_network_prediction"]
            nn_pred = ModelPrediction(
                signal=nn_data["signal"],
                confidence_score=nn_data["confidence_score"],
                class_=nn_data["class"],
                probabilities=nn_data["probabilities"],
            )
        
        rf_pred = None
        if result.get("random_forest_prediction"):
            rf_data = result["random_forest_prediction"]
            rf_pred = ModelPrediction(
                signal=rf_data["signal"],
                confidence_score=rf_data["confidence_score"],
                class_=rf_data["class"],
                probabilities=rf_data["probabilities"],
            )
        
        response = MLPredictResponse(
            signal=result["signal"],
            confidence_score=result["confidence_score"],
            model_used=result["model_used"],
            latency_ms=result["latency_ms"],
            neural_network_prediction=nn_pred,
            random_forest_prediction=rf_pred,
        )
        
        return response
        
    except ValueError as e:
        # Handle missing data, invalid inputs
        logger.warning("Prediction request failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        # Handle model not loaded errors
        logger.error("Model inference error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML models not available. Please ensure models are loaded at startup.",
        )
    except Exception as e:
        # Handle other errors
        logger.error("Unexpected error during prediction: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during prediction.",
        )

