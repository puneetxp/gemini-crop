from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.crop import Crop
from app.services.crop_service import get_service


router = APIRouter(prefix="/ipublic/crop", tags=["ipublic-crop"])
service = get_service()

@router.get("/{item_id}", response_model=Crop)
def show_ipublic_crop(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop not found")
    return record
