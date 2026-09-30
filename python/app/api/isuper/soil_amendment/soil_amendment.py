from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.soil_amendment import SoilAmendment, SoilAmendmentInput
from app.services.soil_amendment_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/soil_amendment", tags=["isuper-soil_amendment"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SoilAmendment])
def list_isuper_soil_amendment():
    return service.all()

@router.get("/{item_id}", response_model=SoilAmendment)
def show_isuper_soil_amendment(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Soil_amendment not found")
    return record

@router.post("/", response_model=SoilAmendment, status_code=201)
def create_isuper_soil_amendment(payload: SoilAmendmentInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=SoilAmendment)
def update_isuper_soil_amendment(item_id: int, payload: SoilAmendmentInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Soil_amendment not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_soil_amendment(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Soil_amendment not found")
    return {"success": True}
