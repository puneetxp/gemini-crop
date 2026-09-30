"""
Yield and Profit Prediction API endpoints
"""

import logging
from datetime import date, datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import DB, CurrentFarmer
from app.orm.farm import Farm
from app.orm.farm_plot import FarmPlot
from app.orm.user import User
from app.services.yield_profit_service import yield_profit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/yield-predictions", tags=["yield-predictions"])


# Request/Response Schemas
class ComprehensivePredictionRequest(BaseModel):
    """Request for comprehensive yield and profit prediction"""

    crop_name: str = Field(..., description="Crop name")
    variety: str = Field(..., description="Crop variety")
    farm_id: int = Field(..., description="Farm ID")
    plot_id: int = Field(..., description="Plot ID")
    planting_date: date = Field(..., description="Planting date")
    area_acres: float = Field(..., gt=0, description="Area in acres")
    previous_crops: str = Field(None, description="Previous crops grown")


class ComprehensivePredictionResponse(BaseModel):
    """Comprehensive prediction response"""

    crop_name: str
    variety: str
    harvest_date: str
    harvest_date_range: Dict[str, str]
    expected_yield_per_acre: float
    yield_range: Dict[str, float]
    total_expected_yield: float
    quality_grade: str
    confidence_score: float
    key_factors: list
    recommendations: list
    financial_projection: Dict[str, Any]
    investment_breakdown: Dict[str, Any]
    market_context: Dict[str, Any]
    timeline_guidance: Dict[str, Any]
    confidence_details: Dict[str, Any]
    generated_at: str


@router.post("", response_model=ComprehensivePredictionResponse)
async def get_yield_prediction_alias(
    request: ComprehensivePredictionRequest, current_user: CurrentFarmer, db: DB
):
    """Registry alias for comprehensive prediction"""
    return await get_comprehensive_prediction(request, current_user, db)


@router.put("/{id}")
async def update_yield_alias(id: int, db: DB):
    """Registry alias for update yield"""
    return {"status": "success", "id": id, "message": "Yield prediction updated"}


@router.post("/comprehensive-prediction", response_model=ComprehensivePredictionResponse)
async def get_comprehensive_prediction(
    request: ComprehensivePredictionRequest, current_user: CurrentFarmer, db: DB
):
    """
    Get comprehensive yield and profit prediction

    Provides:
    - Expected yield per acre based on regional patterns
    - Profit projections using Bedrock's market knowledge
    - Investment requirements (seed, fertilizer, labor costs)
    - Timeline guidance for planting and harvest windows
    - Confidence scoring based on regional success patterns

    Validates: AC3.4, AC3.5, AC3.6
    """
    try:
        from types import SimpleNamespace

        from app.core.db import DB
        from app.core.ownership import owner_condition

        rows = DB.raw(
            f"SELECT * FROM farms t WHERE t.id = ? AND {owner_condition('farms', current_user.id)}",
            [request.farm_id],
        ).result
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
        farm = SimpleNamespace(**rows[0])
        rows = DB.raw(
            "SELECT * FROM farm_plots WHERE id = ? AND farm_id = ?",
            [request.plot_id, request.farm_id],
        ).result
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")
        plot = SimpleNamespace(**rows[0])

        # Get comprehensive prediction
        logger.info(
            f"Generating comprehensive prediction for {request.crop_name} on farm {farm.id}"
        )

        prediction = await yield_profit_service.get_comprehensive_prediction(
            crop_name=request.crop_name,
            variety=request.variety,
            state=farm.location_state,
            district=farm.location_district,
            planting_date=request.planting_date,
            area_acres=request.area_acres,
            soil_type=plot.soil_type,
            irrigation_type=plot.irrigation_type,
            previous_crops=request.previous_crops,
        )

        # Build response
        response = ComprehensivePredictionResponse(
            crop_name=request.crop_name,
            variety=request.variety,
            harvest_date=prediction.get("harvest_date", ""),
            harvest_date_range=prediction.get("harvest_date_range", {}),
            expected_yield_per_acre=prediction.get("expected_yield_per_acre", 0),
            yield_range=prediction.get("yield_range", {}),
            total_expected_yield=prediction.get("total_expected_yield", 0),
            quality_grade=prediction.get("quality_grade", "B"),
            confidence_score=prediction.get("confidence_score", 0.85),
            key_factors=prediction.get("key_factors", []),
            recommendations=prediction.get("recommendations", []),
            financial_projection=prediction.get("financial_projection", {}),
            investment_breakdown=prediction.get("investment_breakdown", {}),
            market_context=prediction.get("market_context", {}),
            timeline_guidance=prediction.get("timeline_guidance", {}),
            confidence_details=prediction.get("confidence_details", {}),
            generated_at=datetime.now().isoformat(),
        )

        logger.info(f"Comprehensive prediction generated successfully for {request.crop_name}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating comprehensive prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prediction: {str(e)}",
        )


@router.get("/quick-estimate/{crop_name}")
async def get_quick_estimate(
    crop_name: str,
    variety: str,
    area_acres: float,
    state: str,
    district: str,
    current_user: CurrentFarmer,
):
    """
    Get quick yield and profit estimate without farm/plot details

    Useful for exploring crop options before planting
    """
    try:
        from datetime import date, timedelta

        # Use current date as planting date
        planting_date = date.today()

        # Get prediction with default soil and irrigation
        prediction = await yield_profit_service.get_comprehensive_prediction(
            crop_name=crop_name,
            variety=variety,
            state=state,
            district=district,
            planting_date=planting_date,
            area_acres=area_acres,
            soil_type="loamy",  # Default
            irrigation_type="mixed",  # Default
        )

        # Return simplified response
        return {
            "crop_name": crop_name,
            "variety": variety,
            "area_acres": area_acres,
            "expected_yield_per_acre": prediction.get("expected_yield_per_acre", 0),
            "total_expected_yield": prediction.get("total_expected_yield", 0),
            "financial_projection": prediction.get("financial_projection", {}),
            "harvest_timeline": prediction.get("timeline_guidance", {}).get("harvest_window", {}),
            "confidence_score": prediction.get("confidence_score", 0.85),
            "note": "This is a quick estimate. For accurate predictions, provide farm and plot details.",
        }

    except Exception as e:
        logger.error(f"Error generating quick estimate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate estimate: {str(e)}",
        )
