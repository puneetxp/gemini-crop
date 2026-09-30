from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop import Crop, CropInput
from app.services.crop_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/crop", tags=["isuper-crop"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[Crop])
def list_isuper_crop():
    return service.all()

@router.get("/{item_id}", response_model=Crop)
def show_isuper_crop(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop not found")
    return record

@router.post("/", response_model=Crop, status_code=201)
def create_isuper_crop(payload: CropInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=Crop)
def update_isuper_crop(item_id: int, payload: CropInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Crop not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_crop(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Crop not found")
    return {"success": True}
