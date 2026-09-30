from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.weather_forecast import WeatherForecast, WeatherForecastInput
from app.services.weather_forecast_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/weather_forecast", tags=["isuper-weather_forecast"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[WeatherForecast])
def list_isuper_weather_forecast():
    return service.all()

@router.get("/{item_id}", response_model=WeatherForecast)
def show_isuper_weather_forecast(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather_forecast not found")
    return record

@router.post("/", response_model=WeatherForecast, status_code=201)
def create_isuper_weather_forecast(payload: WeatherForecastInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=WeatherForecast)
def update_isuper_weather_forecast(item_id: int, payload: WeatherForecastInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Weather_forecast not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_weather_forecast(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Weather_forecast not found")
    return {"success": True}
