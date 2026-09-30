from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.satellite_observation import SatelliteObservation, SatelliteObservationInput
from app.services.satellite_observation_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/satellite_observation", tags=["islogin-satellite_observation"])
service = get_service()

@router.get("/", response_model=List[SatelliteObservation])
def list_islogin_satellite_observation(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=SatelliteObservation)
def show_islogin_satellite_observation(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Satellite_observation not found")
    return record
