from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop_milestone import CropMilestone, CropMilestoneInput
from app.services.crop_milestone_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/crop_milestone", tags=["isuper-crop_milestone"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[CropMilestone])
def list_isuper_crop_milestone():
    return service.all()

@router.get("/{item_id}", response_model=CropMilestone)
def show_isuper_crop_milestone(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_milestone not found")
    return record

@router.post("/", response_model=CropMilestone, status_code=201)
def create_isuper_crop_milestone(payload: CropMilestoneInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=CropMilestone)
def update_isuper_crop_milestone(item_id: int, payload: CropMilestoneInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Crop_milestone not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_crop_milestone(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Crop_milestone not found")
    return {"success": True}
