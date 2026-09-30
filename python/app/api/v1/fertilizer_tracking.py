"""
Fertilizer Tracking API Endpoints

Provides endpoints for:
- Recording fertilizer applications
- Updating soil response data
- Retrieving application history
- Analyzing fertilizer effectiveness
- Generating usage reports

Validates: Requirements AC9 (Phase 6 - Required)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.services.farm_access import plot_for_user
from app.services.fertilizer_tracking_service import FertilizerTrackingService

router = APIRouter(
    prefix="/fertilizer-tracking",
    tags=["fertilizer-tracking"],
    dependencies=[Depends(get_current_active_user)],
)
# Request/Response Models


class FertilizerApplicationCreate(BaseModel):
    """Request model for creating fertilizer application record"""

    farm_id: int = Field(..., description="Farm ID")
    application_date: datetime = Field(..., description="Date of application")
    fertilizer_type: str = Field(..., description="Type: urea, dap, mop, vermicompost, etc.")
    category: str = Field(..., description="Category: organic or chemical")
    quantity_kg: float = Field(..., gt=0, description="Total quantity applied (kg)")
    cost_total: float = Field(..., ge=0, description="Total cost (₹)")
    plot_id: Optional[int] = Field(None, description="Optional specific plot")
    crop_id: Optional[int] = Field(None, description="Optional associated crop")
    area_applied_hectares: Optional[float] = Field(None, gt=0, description="Area where applied")
    nitrogen_kg: Optional[float] = Field(None, ge=0, description="Nitrogen provided (kg)")
    phosphorus_kg: Optional[float] = Field(None, ge=0, description="Phosphorus provided (kg)")
    potassium_kg: Optional[float] = Field(None, ge=0, description="Potassium provided (kg)")
    application_method: Optional[str] = Field(
        None, description="Method: broadcast, banding, foliar"
    )
    growth_stage: Optional[str] = Field(
        None, description="Crop growth stage: basal, vegetative, flowering"
    )
    days_after_planting: Optional[int] = Field(None, ge=0, description="Days after planting")
    soil_test_before_id: Optional[int] = Field(None, description="Soil test before application")
    weather_conditions: Optional[str] = Field(None, description="Weather during application")
    temperature_celsius: Optional[float] = Field(None, description="Temperature during application")
    rainfall_mm_24h: Optional[float] = Field(None, ge=0, description="Rainfall within 24h")
    recommended_by: Optional[str] = Field(None, description="Source: system, agronomist, farmer")
    recommendation_id: Optional[str] = Field(None, description="Reference to recommendation")
    notes: Optional[str] = Field(None, description="Additional notes")


class SoilResponseUpdate(BaseModel):
    """Request model for updating soil response after fertilizer application"""

    soil_test_after_id: int = Field(..., description="Soil test conducted after application")
    soil_response_notes: Optional[str] = Field(
        None, description="Observed soil response and crop performance"
    )


class FertilizerApplicationResponse(BaseModel):
    """Response model for fertilizer application"""

    id: int
    farm_id: int
    plot_id: Optional[int]
    crop_id: Optional[int]
    application_date: datetime
    fertilizer_type: str
    category: str
    quantity_kg: float
    quantity_per_hectare: Optional[float]
    area_applied_hectares: Optional[float]
    nitrogen_kg: Optional[float]
    phosphorus_kg: Optional[float]
    potassium_kg: Optional[float]
    cost_total: float
    cost_per_kg: float
    cost_per_hectare: Optional[float]
    application_method: Optional[str]
    growth_stage: Optional[str]
    days_after_planting: Optional[int]
    soil_test_before_id: Optional[int]
    soil_test_after_id: Optional[int]
    effectiveness_score: Optional[float]
    soil_response_notes: Optional[str]
    weather_conditions: Optional[str]
    temperature_celsius: Optional[float]
    rainfall_mm_24h: Optional[float]
    recommended_by: Optional[str]
    recommendation_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# API Endpoints


@router.get("", response_model=Dict[str, Any])
async def get_fertilizer_tracking_root():
    """Registry alias for fertilizer tracking root"""
    return {
        "status": "success",
        "message": "Fertilizer tracking system operational",
        "features": ["applications", "effectiveness_analysis", "usage_report"],
    }


@router.post("/applications", response_model=FertilizerApplicationResponse, status_code=201)
async def record_fertilizer_application(
    application: FertilizerApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Record a new fertilizer application

    Tracks:
    - Application date, type, quantity, and cost
    - Nutrient content (N, P, K)
    - Application method and timing
    - Weather conditions during application
    - Link to soil test before application

    Returns the created application record with calculated metrics.
    """
    service = FertilizerTrackingService(db)

    try:
        result = await service.record_application(
            farm_id=application.farm_id,
            application_date=application.application_date,
            fertilizer_type=application.fertilizer_type,
            category=application.category,
            quantity_kg=application.quantity_kg,
            cost_total=application.cost_total,
            plot_id=application.plot_id,
            crop_id=application.crop_id,
            area_applied_hectares=application.area_applied_hectares,
            nitrogen_kg=application.nitrogen_kg,
            phosphorus_kg=application.phosphorus_kg,
            potassium_kg=application.potassium_kg,
            application_method=application.application_method,
            growth_stage=application.growth_stage,
            days_after_planting=application.days_after_planting,
            soil_test_before_id=application.soil_test_before_id,
            weather_conditions=application.weather_conditions,
            temperature_celsius=application.temperature_celsius,
            rainfall_mm_24h=application.rainfall_mm_24h,
            recommended_by=application.recommended_by,
            recommendation_id=application.recommendation_id,
            notes=application.notes,
            user=current_user,
        )
        return result
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/applications/{application_id}/soil-response", response_model=FertilizerApplicationResponse
)
async def update_soil_response(
    application_id: int,
    response_data: SoilResponseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Update fertilizer application with soil test results after application

    Calculates effectiveness score (0-100) based on:
    - Nitrogen improvement (30%)
    - Phosphorus improvement (30%)
    - Potassium improvement (30%)
    - Soil health score improvement (10%)

    Returns updated application with effectiveness score.
    """
    service = FertilizerTrackingService(db)

    try:
        result = await service.update_soil_response(
            application_id=application_id,
            soil_test_after_id=response_data.soil_test_after_id,
            soil_response_notes=response_data.soil_response_notes,
            user=current_user,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/applications", response_model=List[FertilizerApplicationResponse])
async def get_application_history(
    farm_id: int = Query(..., description="Farm ID"),
    plot_id: Optional[int] = Query(None, description="Optional plot filter"),
    crop_id: Optional[int] = Query(None, description="Optional crop filter"),
    start_date: Optional[datetime] = Query(None, description="Optional start date filter"),
    end_date: Optional[datetime] = Query(None, description="Optional end date filter"),
    fertilizer_type: Optional[str] = Query(None, description="Optional fertilizer type filter"),
    category: Optional[str] = Query(
        None, description="Optional category filter (organic/chemical)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get fertilizer application history with optional filters

    Returns list of applications ordered by date (most recent first).
    Includes related farm, plot, crop, and soil test data.
    """
    service = FertilizerTrackingService(db)

    try:
        applications = await service.get_application_history(
            farm_id=farm_id,
            plot_id=plot_id,
            crop_id=crop_id,
            start_date=start_date,
            end_date=end_date,
            fertilizer_type=fertilizer_type,
            category=category,
            user=current_user,
        )
        return applications
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{plot_id}", response_model=List[FertilizerApplicationResponse])
async def get_fertilizer_history_alias(
    plot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Registry alias for fertilizer history by plot"""
    service = FertilizerTrackingService(db)
    # Find farm_id for this plot (owner-scoped; other users' plots are 404)
    try:
        plot_result = plot_for_user(plot_id, current_user)
    except LookupError:
        raise HTTPException(status_code=404, detail="Plot not found")

    return await service.get_application_history(
        farm_id=plot_result.farm_id, plot_id=plot_id, user=current_user
    )


@router.get("/effectiveness-analysis")
async def analyze_fertilizer_effectiveness(
    farm_id: int = Query(..., description="Farm ID"),
    plot_id: Optional[int] = Query(None, description="Optional plot filter"),
    start_date: Optional[datetime] = Query(None, description="Optional start date filter"),
    end_date: Optional[datetime] = Query(None, description="Optional end date filter"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Analyze fertilizer effectiveness with ROI calculations

    Provides:
    - Overall effectiveness metrics
    - Analysis by fertilizer type (cost, quantity, effectiveness, ROI)
    - Analysis by category (organic vs chemical)
    - Recommendations for improvement

    ROI score = (effectiveness / cost_per_kg) - higher is better
    """
    service = FertilizerTrackingService(db)

    try:
        analysis = await service.analyze_fertilizer_effectiveness(
            farm_id=farm_id,
            plot_id=plot_id,
            start_date=start_date,
            end_date=end_date,
            user=current_user,
        )
        return analysis
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage-report")
async def generate_usage_report(
    farm_id: int = Query(..., description="Farm ID"),
    plot_id: Optional[int] = Query(None, description="Optional plot filter"),
    start_date: Optional[datetime] = Query(
        None, description="Optional start date (defaults to 1 year ago)"
    ),
    end_date: Optional[datetime] = Query(None, description="Optional end date (defaults to today)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate comprehensive fertilizer usage report

    Includes:
    - Summary statistics (applications, cost, quantity)
    - Nutrients applied (N, P, K totals)
    - Monthly breakdown by fertilizer type
    - Effectiveness analysis with ROI
    - Cost optimization tips

    Default period: Last 365 days
    """
    service = FertilizerTrackingService(db)

    try:
        report = await service.generate_usage_report(
            farm_id=farm_id,
            plot_id=plot_id,
            start_date=start_date,
            end_date=end_date,
            user=current_user,
        )
        return report
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
