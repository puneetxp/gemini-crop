from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.soil_moisture_data import SoilMoistureData, SoilMoistureDataInput
from app.services.soil_moisture_data_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/soil_moisture_data", tags=["isuper-soil_moisture_data"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SoilMoistureData])
def list_isuper_soil_moisture_data():
    return service.all()

@router.get("/{item_id}", response_model=SoilMoistureData)
def show_isuper_soil_moisture_data(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Soil_moisture_data not found")
    return record

@router.post("/", response_model=SoilMoistureData, status_code=201)
def create_isuper_soil_moisture_data(payload: SoilMoistureDataInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=SoilMoistureData)
def update_isuper_soil_moisture_data(item_id: int, payload: SoilMoistureDataInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Soil_moisture_data not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_soil_moisture_data(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Soil_moisture_data not found")
    return {"success": True}
