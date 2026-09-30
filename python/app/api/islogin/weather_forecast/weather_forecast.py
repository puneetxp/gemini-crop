from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.weather_forecast import WeatherForecast, WeatherForecastInput
from app.services.weather_forecast_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/weather_forecast", tags=["islogin-weather_forecast"])
service = get_service()

@router.get("/", response_model=List[WeatherForecast])
def list_islogin_weather_forecast(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=WeatherForecast)
def show_islogin_weather_forecast(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Weather_forecast not found")
    return record
