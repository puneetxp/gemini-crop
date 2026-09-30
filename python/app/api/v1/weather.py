"""
Weather API Endpoints
Provides weather data, forecasts, and alerts

Task 23.1: Integrate with Weather APIs
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache_manager
from app.core.database import get_db
from app.services.weather_service import WeatherService, get_weather_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])


# Request/Response Models
class CurrentWeatherResponse(BaseModel):
    """Current weather response"""

    temperature: float = Field(..., description="Temperature in Celsius")
    feels_like: float = Field(..., description="Feels like temperature in Celsius")
    humidity: int = Field(..., description="Humidity percentage")
    pressure: int = Field(..., description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    wind_direction: int = Field(..., description="Wind direction in degrees")
    rainfall: float = Field(..., description="Rainfall in mm")
    description: str = Field(..., description="Weather description")
    timestamp: datetime = Field(..., description="Data timestamp")
    source: str = Field(..., description="Data source (IMD or OpenWeatherMap)")


class DailyForecast(BaseModel):
    """Daily forecast data"""

    date: datetime = Field(..., description="Forecast date")
    temp_min: float = Field(..., description="Minimum temperature in Celsius")
    temp_max: float = Field(..., description="Maximum temperature in Celsius")
    humidity: int = Field(..., description="Average humidity percentage")
    rainfall: float = Field(..., description="Expected rainfall in mm")
    wind_speed: float = Field(..., description="Average wind speed in m/s")
    description: str = Field(..., description="Weather description")


class ForecastResponse(BaseModel):
    """Weather forecast response"""

    days: int = Field(..., description="Number of forecast days")
    forecasts: list[DailyForecast] = Field(..., description="Daily forecasts")
    source: str = Field(..., description="Data source")
    retrieved_at: datetime = Field(..., description="Data retrieval timestamp")


class WeatherAlert(BaseModel):
    """Weather alert data"""

    alert_id: str = Field(..., description="Alert identifier")
    severity: str = Field(..., description="Alert severity (low, medium, high, critical)")
    event_type: str = Field(..., description="Event type (heavy_rain, cyclone, etc.)")
    headline: str = Field(..., description="Alert headline")
    description: str = Field(..., description="Alert description")
    start_time: datetime = Field(..., description="Alert start time")
    end_time: datetime = Field(..., description="Alert end time")
    affected_areas: list[str] = Field(..., description="Affected areas")
    source: str = Field(..., description="Data source")


class SeasonalPattern(BaseModel):
    """Seasonal weather pattern"""

    month: int = Field(..., description="Month number (1-12)")
    avg_temp: float = Field(..., description="Average temperature")
    avg_rainfall: float = Field(..., description="Average rainfall")
    avg_humidity: int = Field(..., description="Average humidity")
    monsoon_month: bool = Field(..., description="Is monsoon month")


class SeasonalAnalysisResponse(BaseModel):
    """Seasonal pattern analysis response"""

    latitude: float
    longitude: float
    years_analyzed: int
    monthly_patterns: dict[int, dict]
    monsoon_months: list[int]


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    latitude: float = Query(..., description="GPS latitude", ge=-90, le=90),
    longitude: float = Query(..., description="GPS longitude", ge=-180, le=180),
    use_cache: bool = Query(True, description="Use cached data if available"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current weather data for a location

    - **latitude**: GPS latitude (-90 to 90)
    - **longitude**: GPS longitude (-180 to 180)
    - **use_cache**: Whether to use cached data (default: true)

    Returns current weather conditions including temperature, humidity, rainfall, wind speed.
    Data source: IMD (primary) or OpenWeatherMap (backup).
    """
    try:
        cache_manager = get_cache_manager()
        weather_service = get_weather_service(db, cache_manager=cache_manager)

        async with weather_service:
            weather_data = await weather_service.get_current_weather(latitude, longitude, use_cache)

        if not weather_data:
            raise HTTPException(status_code=503, detail="Weather data unavailable from all sources")

        return CurrentWeatherResponse(**weather_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current weather: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/forecast", response_model=ForecastResponse)
async def get_weather_forecast(
    latitude: float = Query(..., description="GPS latitude", ge=-90, le=90),
    longitude: float = Query(..., description="GPS longitude", ge=-180, le=180),
    days: int = Query(7, description="Number of forecast days (7 or 14)", ge=1, le=14),
    use_cache: bool = Query(True, description="Use cached data if available"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get weather forecast for a location

    - **latitude**: GPS latitude (-90 to 90)
    - **longitude**: GPS longitude (-180 to 180)
    - **days**: Number of forecast days (7 or 14, default: 7)
    - **use_cache**: Whether to use cached data (default: true)

    Returns daily weather forecast including temperature range, rainfall, humidity, wind speed.
    Data source: IMD (primary) or OpenWeatherMap (backup, max 5 days).
    Cache TTL: 1 hour.
    """
    try:
        cache_manager = get_cache_manager()
        weather_service = get_weather_service(db, cache_manager=cache_manager)

        async with weather_service:
            forecast_data = await weather_service.get_forecast(latitude, longitude, days, use_cache)

        if not forecast_data:
            raise HTTPException(
                status_code=503, detail="Weather forecast unavailable from all sources"
            )

        return ForecastResponse(**forecast_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/alerts", response_model=list[WeatherAlert])
async def get_weather_alerts(
    latitude: Optional[float] = Query(None, description="GPS latitude", ge=-90, le=90),
    longitude: Optional[float] = Query(None, description="GPS longitude", ge=-180, le=180),
    state: Optional[str] = Query(None, description="State name"),
    district: Optional[str] = Query(None, description="District name"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get weather alerts for a location

    - **latitude**: GPS latitude (optional)
    - **longitude**: GPS longitude (optional)
    - **state**: State name (optional, for IMD)
    - **district**: District name (optional, for IMD)

    Returns active weather alerts including severity, event type, affected areas.
    Provide either GPS coordinates OR state (with optional district).
    Data source: IMD (primary) or OpenWeatherMap (backup).
    """
    if not (latitude and longitude) and not state:
        raise HTTPException(
            status_code=400, detail="Provide either GPS coordinates (latitude, longitude) or state"
        )

    try:
        cache_manager = get_cache_manager()
        weather_service = get_weather_service(db, cache_manager=cache_manager)

        async with weather_service:
            alerts = await weather_service.get_weather_alerts(latitude, longitude, state, district)

        return [WeatherAlert(**alert) for alert in alerts]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/seasonal-analysis", response_model=SeasonalAnalysisResponse)
async def get_seasonal_analysis(
    latitude: float = Query(..., description="GPS latitude", ge=-90, le=90),
    longitude: float = Query(..., description="GPS longitude", ge=-180, le=180),
    years: int = Query(3, description="Number of years to analyze", ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """
    Get seasonal weather pattern analysis

    - **latitude**: GPS latitude (-90 to 90)
    - **longitude**: GPS longitude (-180 to 180)
    - **years**: Number of years to analyze (1-10, default: 3)

    Returns seasonal weather patterns including:
    - Monthly average temperature, rainfall, humidity
    - Monsoon month identification
    - Historical trends

    Used for crop recommendation refinement and planting window optimization.
    """
    try:
        cache_manager = get_cache_manager()
        weather_service = get_weather_service(db, cache_manager=cache_manager)

        async with weather_service:
            analysis = await weather_service.analyze_seasonal_patterns(latitude, longitude, years)

        if not analysis:
            raise HTTPException(
                status_code=404, detail="Insufficient historical data for seasonal analysis"
            )

        return SeasonalAnalysisResponse(**analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing seasonal analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
