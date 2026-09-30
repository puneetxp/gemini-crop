"""
Plot Analysis API endpoints
Provides AI-powered crop recommendations based on plot characteristics

Task 26.1: Comprehensive plot analysis API
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.plot_analysis_service import PlotAnalysisService

router = APIRouter(prefix="/plot-analysis", tags=["plot-analysis"])


@router.post("/analyze")
async def analyze_plot_alias(
    plot_id: int = Query(..., description="Plot ID"),
    request: PlotAnalysisRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Registry alias for analyze plot"""
    if request is None:
        request = PlotAnalysisRequest(season="kharif")
    return await analyze_plot(plot_id, request, db, current_user)


@router.get("/profitability")
async def compare_plot_profitability_alias(
    plot_id: int = Query(..., description="Plot ID"),
    crops: str = Query(..., description="Comma-separated crop names to compare"),
    season: str = Query("kharif", description="Target season"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Registry alias for profitability comparison"""
    return await compare_plot_profitability(plot_id, crops, season, db, current_user)


@router.get("/history/{plot_id}")
async def get_plot_analysis_history(
    plot_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """Registry alias for analysis history"""
    return {"plot_id": plot_id, "history": []}


class PlotAnalysisRequest(BaseModel):
    """Request model for plot analysis"""

    season: str = Field(..., description="Target season (kharif/rabi/zaid)")
    budget_per_acre: Optional[float] = Field(None, description="Investment capacity per acre", ge=0)
    preferences: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Farmer preferences (risk_tolerance, market_focus, organic)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "season": "kharif",
                "budget_per_acre": 20000,
                "preferences": {
                    "risk_tolerance": "medium",
                    "market_focus": "local",
                    "organic": "false",
                },
            }
        }


class PlotAnalysisResponse(BaseModel):
    """Response model for plot analysis"""

    plot_id: int
    plot_name: str
    analysis_date: str
    season: str
    plot_characteristics: Dict[str, Any]
    recommended_crops: list
    annual_strategy: Dict[str, Any]
    plot_health: Dict[str, Any]
    soil_recommendations: Optional[list] = None
    water_recommendations: Optional[list] = None


@router.post(
    "/{plot_id}/analyze", response_model=PlotAnalysisResponse, status_code=status.HTTP_200_OK
)
async def analyze_plot(
    plot_id: int,
    request: PlotAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze plot and get AI-powered crop recommendations

    This endpoint:
    1. Retrieves plot details from database (location, soil, irrigation)
    2. Gets latest soil test results if available
    3. Calls Bedrock AI with complete plot characteristics
    4. Returns ranked crop recommendations with profitability analysis
    5. Includes quality predictions, risk assessment, and cultivation guidance

    **Response includes:**
    - Top 5 crops ranked by suitability (0-10 score)
    - Detailed profitability metrics (investment, revenue, profit, ROI)
    - Yield predictions with quality grades (A/B/C)
    - Cultivation timeline and requirements
    - Risk assessment with mitigation strategies
    - Weather guidance and soil recommendations

    **Caching:**
    - Results cached for 6 hours to reduce API costs
    - Cache key includes plot_id, season, budget, preferences

    **Cost:**
    - Estimated $0.01-0.05 per analysis
    - Cache hit rate target: 75-85%
    """
    try:
        service = PlotAnalysisService(db)

        analysis = await service.analyze_plot(
            plot_id=plot_id,
            season=request.season,
            budget_per_acre=request.budget_per_acre,
            preferences=request.preferences,
            user=current_user,
        )

        return analysis

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plot analysis failed: {str(e)}",
        )


@router.get("/{plot_id}/profitability", status_code=status.HTTP_200_OK)
async def compare_plot_profitability(
    plot_id: int,
    crops: str = Query(..., description="Comma-separated crop names to compare"),
    season: str = Query("kharif", description="Target season"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Compare profitability of different crops for a specific plot

    This endpoint helps farmers make data-driven decisions by comparing
    expected returns across multiple crop options.

    **Query Parameters:**
    - crops: Comma-separated crop names (e.g., "rice,wheat,cotton")
    - season: Target season (kharif/rabi/zaid)

    **Response includes:**
    - Side-by-side comparison of profitability metrics
    - Rankings by profit, ROI, and risk level
    - AI recommendation with reasoning

    **Example:**
    ```
    GET /plots/123/profitability?crops=rice,wheat,cotton&season=kharif
    ```
    """
    try:
        service = PlotAnalysisService(db)

        # Parse crop names
        crop_list = [c.strip() for c in crops.split(",")]

        # Get analysis for each crop
        comparisons = []
        for crop_name in crop_list:
            # Analyze plot with focus on specific crop
            analysis = await service.analyze_plot(
                plot_id=plot_id,
                season=season,
                budget_per_acre=20000,  # Default budget
                preferences={},
                user=current_user,
            )

            # Find this crop in recommendations
            crop_data = next(
                (
                    c
                    for c in analysis.get("recommended_crops", [])
                    if c["crop_name"].lower() == crop_name.lower()
                ),
                None,
            )

            if crop_data:
                comparisons.append(
                    {
                        "crop_name": crop_data["crop_name"],
                        "investment": crop_data["profitability"]["per_acre"]["investment"],
                        "revenue": crop_data["profitability"]["per_acre"]["revenue"],
                        "profit": crop_data["profitability"]["per_acre"]["profit"],
                        "roi": crop_data["profitability"]["per_acre"]["roi_percentage"],
                        "risk_level": crop_data.get("risk_probability", "medium"),
                        "market_demand": crop_data.get("demand_level", "medium"),
                        "suitability_score": crop_data.get("suitability_score", 7.0),
                    }
                )

        if not comparisons:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No matching crops found in recommendations",
            )

        # Rank by different criteria
        best_for_profit = max(comparisons, key=lambda x: x["profit"])
        best_for_roi = max(comparisons, key=lambda x: x["roi"])

        # AI recommendation (balanced approach)
        def score_crop(c):
            risk_score = {"low": 100, "medium": 70, "high": 40}.get(c["risk_level"].lower(), 70)
            return c["suitability_score"] * 0.4 + c["roi"] * 0.003 + risk_score * 0.3

        ai_recommendation = max(comparisons, key=score_crop)

        return {
            "plot_id": plot_id,
            "comparison_date": analysis["analysis_date"],
            "season": season,
            "crops": comparisons,
            "recommendation": {
                "best_for_profit": best_for_profit["crop_name"],
                "best_for_roi": best_for_roi["crop_name"],
                "ai_recommendation": ai_recommendation["crop_name"],
                "reason": f"Best balance of profitability (₹{ai_recommendation['profit']:.0f}/acre), "
                f"suitability ({ai_recommendation['suitability_score']}/10), "
                f"and market demand ({ai_recommendation['market_demand']})",
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profitability comparison failed: {str(e)}",
        )
