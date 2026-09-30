"""
Hybrid AI API Endpoints

Provides endpoints for hybrid AI predictions and analytics.
Routes intelligently between SageMaker and Bedrock based on query type.

Compatible with Python 3.14.3, FastAPI 0.115.6
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_admin
from app.services.hybrid_ai_service import ModelType, QueryType, hybrid_ai_service

router = APIRouter(
    prefix="/hybrid-ai", tags=["Hybrid AI"], dependencies=[Depends(get_current_admin)]
)
# ==================== Request/Response Models ====================


class YieldPredictionRequest(BaseModel):
    """Request model for yield prediction"""

    crop_name: str = Field(..., description="Crop name")
    variety: str = Field(..., description="Crop variety")
    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name")
    planting_date: str = Field(..., description="Planting date (YYYY-MM-DD)")
    area_acres: float = Field(..., gt=0, description="Area in acres")
    soil_type: str = Field(..., description="Soil type")
    irrigation_type: str = Field(..., description="Irrigation type")
    force_model: Optional[str] = Field(None, description="Force specific model (sagemaker/bedrock)")


class YieldPredictionResponse(BaseModel):
    """Response model for yield prediction"""

    expected_yield_per_acre: Optional[float] = Field(None, description="Expected yield per acre")
    yield_range: Optional[Dict[str, float]] = Field(None, description="Yield range (min/max)")
    total_expected_yield: Optional[float] = Field(None, description="Total expected yield")
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    model_used: str = Field(..., description="Model used (sagemaker/bedrock)")
    model_accuracy: str = Field(..., description="Model accuracy range")
    prediction_method: str = Field(..., description="Prediction method")
    cost_estimate_inr: float = Field(..., description="Cost estimate in INR")
    timestamp: str = Field(..., description="Prediction timestamp")
    fallback: Optional[bool] = Field(None, description="Whether fallback was used")


class AnnualStrategyRequest(BaseModel):
    """Request model for annual strategy"""

    state: str = Field(..., description="State name")
    district: str = Field(..., description="District name")
    soil_type: str = Field(..., description="Soil type")
    area_acres: float = Field(..., gt=0, description="Area in acres")
    irrigation_type: str = Field(..., description="Irrigation type")
    previous_crops: Optional[str] = Field(None, description="Previous crops grown")
    budget_per_acre: Optional[float] = Field(None, gt=0, description="Budget per acre")


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions"""

    predictions: List[YieldPredictionRequest] = Field(
        ..., description="List of prediction requests"
    )
    use_sagemaker: bool = Field(True, description="Use SageMaker batch inference")


class CostReportResponse(BaseModel):
    """Response model for cost report"""

    total_calls: int
    sagemaker_calls: int
    bedrock_calls: int
    total_cost_inr: float
    sagemaker_cost_inr: float
    bedrock_cost_inr: float
    cost_per_prediction_inr: float
    savings_vs_bedrock_only_inr: float
    savings_percentage: float
    target_cost_per_prediction: float
    meets_target: bool


class PerformanceReportResponse(BaseModel):
    """Response model for performance report"""

    total_calls: int
    total_errors: int
    routing_accuracy: float
    sagemaker_performance: Dict[str, Any]
    bedrock_performance: Dict[str, Any]
    cache_hit_rate: float
    fallback_success_rate: float
    target_routing_accuracy: float
    meets_target: bool


# ==================== Prediction Endpoints ====================


@router.post("/predict-yield", response_model=YieldPredictionResponse)
async def predict_yield(request: YieldPredictionRequest):
    """
    Predict crop yield using hybrid AI approach.

    Routes to SageMaker for complex predictions (92-95% accuracy),
    falls back to Bedrock if unavailable (85-90% accuracy).

    **Cost Optimization:**
    - SageMaker: ~₹0.17 per prediction
    - Bedrock: ~₹4.15 per prediction
    - Target: < ₹3 per prediction

    **Caching:**
    - Results cached for 6 hours
    - Reduces API costs and improves response time
    """
    try:
        # Parse force_model if provided
        force_model = None
        if request.force_model:
            if request.force_model.lower() == "sagemaker":
                force_model = ModelType.SAGEMAKER
            elif request.force_model.lower() == "bedrock":
                force_model = ModelType.BEDROCK

        result = await hybrid_ai_service.predict_crop_yield(
            crop_name=request.crop_name,
            variety=request.variety,
            state=request.state,
            district=request.district,
            planting_date=request.planting_date,
            area_acres=request.area_acres,
            soil_type=request.soil_type,
            irrigation_type=request.irrigation_type,
            force_model=force_model,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annual-strategy")
async def get_annual_strategy(request: AnnualStrategyRequest):
    """
    Get comprehensive annual crop strategy using Bedrock.

    Provides Kharif, Rabi, and Zaid season recommendations with:
    - Crop recommendations
    - Profit estimates
    - Investment requirements
    - Month-by-month action plan
    - Weather-aware guidance

    **Model:** Always uses Bedrock (general reasoning)
    **Cost:** ~₹4.15 per strategy
    **Caching:** 6-hour TTL
    """
    try:
        result = await hybrid_ai_service.get_annual_strategy(
            state=request.state,
            district=request.district,
            soil_type=request.soil_type,
            area_acres=request.area_acres,
            irrigation_type=request.irrigation_type,
            previous_crops=request.previous_crops,
            budget_per_acre=request.budget_per_acre,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crop-recommendations")
async def get_crop_recommendations(
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    season: str = Query(..., description="Season (kharif/rabi/zaid)"),
    soil_type: str = Query(..., description="Soil type"),
    area_acres: float = Query(..., gt=0, description="Area in acres"),
    irrigation_type: str = Query(..., description="Irrigation type"),
):
    """
    Get top crop recommendations for a specific season using Bedrock.

    Returns ranked list of suitable crops with:
    - Suitability reasons
    - Expected yields and profits
    - Investment requirements
    - Market demand levels

    **Model:** Always uses Bedrock (general reasoning)
    **Cost:** ~₹4.15 per request
    **Caching:** 6-hour TTL
    """
    try:
        recommendations = await hybrid_ai_service.get_crop_recommendations(
            state=state,
            district=district,
            season=season,
            soil_type=soil_type,
            area_acres=area_acres,
            irrigation_type=irrigation_type,
        )

        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-predict")
async def batch_predict_yields(request: BatchPredictionRequest):
    """
    Batch inference for multiple yield predictions (cost optimization).

    **Cost Optimization:**
    - SageMaker batch: More cost-effective for large batches
    - Bedrock: Better for small batches (< 10 predictions)

    **Caching:**
    - Individual predictions cached for 6 hours
    - Reduces redundant API calls
    """
    try:
        predictions_list = [pred.model_dump() for pred in request.predictions]

        results = await hybrid_ai_service.batch_predict_yields(
            predictions=predictions_list, use_sagemaker=request.use_sagemaker
        )

        return {
            "total_predictions": len(results),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Analytics Endpoints ====================


@router.get("/cost-report", response_model=CostReportResponse)
async def get_cost_report():
    """
    Get cost report for hybrid AI usage.

    Provides breakdown of:
    - Total costs by model
    - Cost per prediction
    - Savings vs Bedrock-only approach
    - Target achievement status

    **Target:** < ₹3 per prediction (vs ₹5 Bedrock baseline)
    """
    try:
        report = hybrid_ai_service.get_cost_report()
        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-report", response_model=PerformanceReportResponse)
async def get_performance_report():
    """
    Get performance report for hybrid AI system.

    Provides metrics on:
    - Routing accuracy
    - Model performance (calls, errors, error rates)
    - Cache hit rate
    - Fallback success rate

    **Targets:**
    - Routing accuracy: > 98%
    - Fallback success rate: 100%
    - Cache hit rate: > 70%
    """
    try:
        report = hybrid_ai_service.get_performance_report()
        return report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing-statistics")
async def get_routing_statistics():
    """
    Get routing statistics by query type.

    Shows how queries are distributed between SageMaker and Bedrock
    for different query types.
    """
    try:
        stats = hybrid_ai_service.get_routing_statistics()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check ====================


@router.get("/health")
async def health_check():
    """
    Health check for hybrid AI service.

    Returns status of SageMaker and Bedrock availability.
    """
    return {
        "status": "healthy",
        "sagemaker_enabled": hybrid_ai_service.sagemaker_enabled,
        "bedrock_enabled": hybrid_ai_service.bedrock_enabled,
        "timestamp": datetime.utcnow().isoformat(),
    }
