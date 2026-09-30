from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.soil_moisture_data import SoilMoistureData, SoilMoistureDataInput
from app.services.soil_moisture_data_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/soil_moisture_data", tags=["islogin-soil_moisture_data"])
service = get_service()

@router.get("/", response_model=List[SoilMoistureData])
def list_islogin_soil_moisture_data(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=SoilMoistureData)
def show_islogin_soil_moisture_data(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Soil_moisture_data not found")
    return record
