from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.crop_market_data import CropMarketData, CropMarketDataInput
from app.services.crop_market_data_service import get_service


router = APIRouter(prefix="/ipublic/crop_market_data", tags=["ipublic-crop_market_data"])
service = get_service()

@router.get("/{item_id}", response_model=CropMarketData)
def show_ipublic_crop_market_data(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_market_data not found")
    return record
