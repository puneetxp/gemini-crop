from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop_profitability import CropProfitability, CropProfitabilityInput
from app.services.crop_profitability_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/crop_profitability", tags=["islogin-crop_profitability"])
service = get_service()

@router.get("/", response_model=List[CropProfitability])
def list_islogin_crop_profitability(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=CropProfitability)
def show_islogin_crop_profitability(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_profitability not found")
    return record
