from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.weather_alert import WeatherAlert, WeatherAlertInput
from app.services.weather_alert_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/weather_alert", tags=["islogin-weather_alert"])
service = get_service()

@router.get("/", response_model=List[WeatherAlert])
def list_islogin_weather_alert(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=WeatherAlert)
def show_islogin_weather_alert(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Weather_alert not found")
    return record
