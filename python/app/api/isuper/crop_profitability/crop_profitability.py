from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop_profitability import CropProfitability, CropProfitabilityInput
from app.services.crop_profitability_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/crop_profitability", tags=["isuper-crop_profitability"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[CropProfitability])
def list_isuper_crop_profitability():
    return service.all()

@router.get("/{item_id}", response_model=CropProfitability)
def show_isuper_crop_profitability(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_profitability not found")
    return record

@router.post("/", response_model=CropProfitability, status_code=201)
def create_isuper_crop_profitability(payload: CropProfitabilityInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=CropProfitability)
def update_isuper_crop_profitability(item_id: int, payload: CropProfitabilityInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Crop_profitability not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_crop_profitability(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Crop_profitability not found")
    return {"success": True}
