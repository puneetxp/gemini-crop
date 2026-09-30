from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.crop_profitability import CropProfitability, CropProfitabilityInput
from app.services.crop_profitability_service import get_service
from typing import List


router = APIRouter(prefix="/ipublic/crop_profitability", tags=["ipublic-crop_profitability"])
service = get_service()

@router.get("/", response_model=List[CropProfitability])
def list_ipublic_crop_profitability():
    return service.all()

@router.get("/{item_id}", response_model=CropProfitability)
def show_ipublic_crop_profitability(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_profitability not found")
    return record
