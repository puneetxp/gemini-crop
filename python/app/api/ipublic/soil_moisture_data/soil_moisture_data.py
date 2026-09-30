from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.soil_moisture_data import SoilMoistureData, SoilMoistureDataInput
from app.services.soil_moisture_data_service import get_service


router = APIRouter(prefix="/ipublic/soil_moisture_data", tags=["ipublic-soil_moisture_data"])
service = get_service()

@router.get("/{item_id}", response_model=SoilMoistureData)
def show_ipublic_soil_moisture_data(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Soil_moisture_data not found")
    return record
