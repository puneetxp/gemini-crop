from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.satellite_observation import SatelliteObservation, SatelliteObservationInput
from app.services.satellite_observation_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/satellite_observation", tags=["isuper-satellite_observation"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SatelliteObservation])
def list_isuper_satellite_observation():
    return service.all()

@router.get("/{item_id}", response_model=SatelliteObservation)
def show_isuper_satellite_observation(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Satellite_observation not found")
    return record

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_satellite_observation(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Satellite_observation not found")
    return {"success": True}
