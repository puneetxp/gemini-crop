"""
Predictive Analytics API Endpoints

Provides AI-powered predictive analytics for market intelligence
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.services.predictive_analytics_service import PredictiveAnalyticsService

router = APIRouter(
    prefix="/predictive-analytics",
    tags=["Predictive Analytics"],
    dependencies=[Depends(get_current_active_user)],
)


@router.post("/predict-price")
async def predict_price(
    item_type: str = Query(..., description="crop or livestock"),
    item_name: str = Query(..., description="Name of crop or livestock"),
    state: str = Query(..., description="State for prediction"),
    district: Optional[str] = Query(None, description="District for more specific prediction"),
    variety: Optional[str] = Query(None, description="Variety or breed"),
    forecast_days: int = Query(30, ge=30, le=90, description="Days to forecast (30-90)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict future prices using Amazon Bedrock AI

    - **item_type**: 'crop' or 'livestock'
    - **item_name**: Name of the crop or livestock
    - **state**: State for prediction
    - **district**: Optional district for more specific prediction
    - **variety**: Optional variety or breed
    - **forecast_days**: Number of days to forecast (30-90)

    Returns price prediction with confidence score, range, and trend
    """
    service = PredictiveAnalyticsService(db)

    try:
        result = await service.predict_price(
            item_type=item_type,
            item_name=item_name,
            state=state,
            district=district,
            variety=variety,
            forecast_days=forecast_days,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/predict-demand")
async def predict_demand(
    item_type: str = Query(..., description="crop or livestock"),
    item_name: str = Query(..., description="Name of crop or livestock"),
    state: str = Query(..., description="State for prediction"),
    district: Optional[str] = Query(None, description="District for more specific prediction"),
    forecast_days: int = Query(30, ge=7, le=90, description="Days to forecast (7-90)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict future demand based on buyer interest patterns

    Returns demand forecast with confidence score and growth rate
    """
    service = PredictiveAnalyticsService(db)

    try:
        result = await service.predict_demand(
            item_type=item_type,
            item_name=item_name,
            state=state,
            district=district,
            forecast_days=forecast_days,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demand prediction failed: {str(e)}")


@router.get("/supply-demand-gaps")
async def get_supply_demand_gaps(
    state: str = Query(..., description="State to analyze"),
    district: Optional[str] = Query(None, description="District to analyze"),
    item_type: Optional[str] = Query(None, description="Filter by item type (crop/livestock)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Identify supply-demand gaps in the market

    Returns list of items with supply-demand imbalances, sorted by severity
    """
    service = PredictiveAnalyticsService(db)

    try:
        result = await service.identify_supply_demand_gaps(
            state=state, district=district, item_type=item_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


@router.get("/opportunity-score")
async def get_opportunity_score(
    item_type: str = Query(..., description="crop or livestock"),
    item_name: str = Query(..., description="Name of crop or livestock"),
    state: str = Query(..., description="State for analysis"),
    district: Optional[str] = Query(None, description="District for more specific analysis"),
    variety: Optional[str] = Query(None, description="Variety or breed"),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate opportunity score for farmers (0-100 scale)

    Factors:
    - Price trend (30%)
    - Demand level (30%)
    - Supply-demand gap (20%)
    - Historical profitability (20%)

    Returns opportunity score with breakdown and recommendation
    """
    service = PredictiveAnalyticsService(db)

    try:
        result = await service.calculate_opportunity_score(
            item_type=item_type,
            item_name=item_name,
            state=state,
            district=district,
            variety=variety,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Opportunity score calculation failed: {str(e)}"
        )


@router.post("/generate-opportunity-alerts")
async def generate_opportunity_alerts(
    farmer_id: Optional[int] = Query(
        None, description="Farmer user ID (defaults to you; admins may pass any)"
    ),
    state: str = Query(..., description="Farmer's state"),
    district: Optional[str] = Query(None, description="Farmer's district"),
    min_score: int = Query(
        70, ge=0, le=100, description="Minimum opportunity score to trigger alert"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate market opportunity alerts for farmers

    Identifies high-opportunity crops and sends SNS notifications

    Returns list of opportunities and SNS message IDs
    """
    if farmer_id is None or getattr(current_user, "user_type", None) != "admin":
        farmer_id = current_user.id
    service = PredictiveAnalyticsService(db)

    try:
        result = await service.generate_market_opportunity_alert(
            farmer_id=farmer_id, state=state, district=district, min_score=min_score
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert generation failed: {str(e)}")


@router.get("/buyer-supply-planning")
async def get_buyer_supply_planning(
    item_type: str = Query(..., description="crop or livestock"),
    item_name: str = Query(..., description="Name of crop or livestock"),
    state: str = Query(..., description="State for planning"),
    district: Optional[str] = Query(None, description="District for more specific planning"),
    months_ahead: int = Query(3, ge=1, le=6, description="Planning horizon in months (1-6)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Provide supply planning data for buyers

    Shows upcoming supply availability, price forecasts, and quality predictions

    Returns monthly supply breakdown with price forecasts
    """
    service = PredictiveAnalyticsService(db)

    try:
        result = await service.get_buyer_supply_planning_data(
            item_type=item_type,
            item_name=item_name,
            state=state,
            district=district,
            months_ahead=months_ahead,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supply planning failed: {str(e)}")
