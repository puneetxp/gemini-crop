from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.weather_forecast import WeatherForecast, WeatherForecastInput
from app.services.weather_forecast_service import get_service
from typing import List


router = APIRouter(prefix="/ipublic/weather_forecast", tags=["ipublic-weather_forecast"])
service = get_service()

@router.get("/", response_model=List[WeatherForecast])
def list_ipublic_weather_forecast():
    return service.all()

@router.get("/{item_id}", response_model=WeatherForecast)
def show_ipublic_weather_forecast(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather_forecast not found")
    return record
