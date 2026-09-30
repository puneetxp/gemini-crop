from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.weather_alert import WeatherAlert, WeatherAlertInput
from app.services.weather_alert_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/weather_alert", tags=["isuper-weather_alert"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[WeatherAlert])
def list_isuper_weather_alert():
    return service.all()

@router.get("/{item_id}", response_model=WeatherAlert)
def show_isuper_weather_alert(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather_alert not found")
    return record

@router.post("/", response_model=WeatherAlert, status_code=201)
def create_isuper_weather_alert(payload: WeatherAlertInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=WeatherAlert)
def update_isuper_weather_alert(item_id: int, payload: WeatherAlertInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Weather_alert not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_weather_alert(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Weather_alert not found")
    return {"success": True}
