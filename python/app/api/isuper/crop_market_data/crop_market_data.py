from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop_market_data import CropMarketData, CropMarketDataInput
from app.services.crop_market_data_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/crop_market_data", tags=["isuper-crop_market_data"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[CropMarketData])
def list_isuper_crop_market_data():
    return service.all()

@router.get("/{item_id}", response_model=CropMarketData)
def show_isuper_crop_market_data(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_market_data not found")
    return record

@router.post("/", response_model=CropMarketData, status_code=201)
def create_isuper_crop_market_data(payload: CropMarketDataInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=CropMarketData)
def update_isuper_crop_market_data(item_id: int, payload: CropMarketDataInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Crop_market_data not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_crop_market_data(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Crop_market_data not found")
    return {"success": True}
