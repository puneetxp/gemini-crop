"""
Weather-Based Recommendations API
Provides weather-aware farming recommendations

Task 23.3: Build weather-based recommendations
Validates: Requirements AC8 (Phase 6 - Required)
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.cache import get_cache_manager
from app.core.database import get_db
from app.services.severe_weather_service import get_severe_weather_service
from app.services.weather_recommendations_service import get_weather_recommendations_service
from app.services.weather_service import get_weather_service

router = APIRouter(
    prefix="/weather-recommendations",
    tags=["weather-recommendations"],
    dependencies=[Depends(get_current_active_user)],
)


@router.get("")
async def get_weather_recommendations_root():
    """Registry alias for weather recommendations root"""
    return {
        "status": "success",
        "message": "Weather recommendations system operational",
        "features": ["planting", "harvest_timing", "irrigation", "crop_care"],
    }


@router.get("/planting")
async def get_planting_recommendations(
    latitude: float = Query(..., description="GPS latitude"),
    longitude: float = Query(..., description="GPS longitude"),
    crop_type: str = Query(..., description="Type of crop to plant"),
    season: str = Query(..., description="Growing season (kharif, rabi, zaid)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get weather-aware planting recommendations

    Returns optimal planting windows based on rainfall forecast
    """
    cache_manager = get_cache_manager()
    weather_service = get_weather_service(db, cache_manager=cache_manager)
    severe_weather_service = get_severe_weather_service(db, weather_service)
    recommendations_service = get_weather_recommendations_service(
        db, weather_service, severe_weather_service
    )

    try:
        result = await recommendations_service.get_planting_recommendations(
            latitude, longitude, crop_type, season
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await weather_service.close()


@router.get("/harvest-timing")
async def get_harvest_timing_recommendations(
    farm_id: int = Query(..., description="Farm ID"),
    crop_id: int = Query(..., description="Crop ID"),
    expected_harvest_date: date = Query(..., description="Expected harvest date"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get optimal harvest timing based on weather windows

    Identifies dry periods to avoid rain during harvest
    """
    cache_manager = get_cache_manager()
    weather_service = get_weather_service(db, cache_manager=cache_manager)
    severe_weather_service = get_severe_weather_service(db, weather_service)
    recommendations_service = get_weather_recommendations_service(
        db, weather_service, severe_weather_service
    )

    try:
        result = await recommendations_service.get_harvest_timing_recommendations(
            farm_id, crop_id, expected_harvest_date, user=current_user
        )
        return result
    except LookupError as e:  # someone else's (or a missing) farm / crop
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await weather_service.close()


@router.get("/irrigation-schedule")
async def get_irrigation_schedule(
    latitude: float = Query(..., description="GPS latitude"),
    longitude: float = Query(..., description="GPS longitude"),
    crop_type: str = Query(..., description="Type of crop"),
    soil_type: str = Query(..., description="Soil type (sandy, loamy, clay)"),
    days_ahead: int = Query(7, description="Number of days to schedule", ge=1, le=14),
    db: AsyncSession = Depends(get_db),
):
    """
    Get irrigation schedule based on rainfall forecasts

    Reduces water waste by accounting for expected rainfall
    """
    cache_manager = get_cache_manager()
    weather_service = get_weather_service(db, cache_manager=cache_manager)
    severe_weather_service = get_severe_weather_service(db, weather_service)
    recommendations_service = get_weather_recommendations_service(
        db, weather_service, severe_weather_service
    )

    try:
        result = await recommendations_service.get_irrigation_schedule(
            latitude, longitude, crop_type, soil_type, days_ahead
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await weather_service.close()


@router.get("/crop-care")
async def get_crop_care_recommendations(
    latitude: float = Query(..., description="GPS latitude"),
    longitude: float = Query(..., description="GPS longitude"),
    crop_type: str = Query(..., description="Type of crop"),
    growth_stage: str = Query(
        ..., description="Growth stage (germination, vegetative, flowering, maturation)"
    ),
    days_ahead: int = Query(7, description="Number of days to plan", ge=1, le=14),
    db: AsyncSession = Depends(get_db),
):
    """
    Get weather-based crop care recommendations

    Provides optimal timing for pest control and fertilizer application
    """
    cache_manager = get_cache_manager()
    weather_service = get_weather_service(db, cache_manager=cache_manager)
    severe_weather_service = get_severe_weather_service(db, weather_service)
    recommendations_service = get_weather_recommendations_service(
        db, weather_service, severe_weather_service
    )

    try:
        result = await recommendations_service.get_crop_care_recommendations(
            latitude, longitude, crop_type, growth_stage, days_ahead
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await weather_service.close()
