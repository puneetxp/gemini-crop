from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop import Crop, CropInput
from app.services.crop_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/crop", tags=["islogin-crop"])
service = get_service()

@router.get("/", response_model=List[Crop])
def list_islogin_crop(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=Crop)
def show_islogin_crop(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Crop not found")
    return record

@router.post("/", response_model=Crop, status_code=201)
def create_islogin_crop(payload: CropInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=Crop)
def update_islogin_crop(item_id: int, payload: CropInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Crop not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_crop(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Crop not found")
    return {"success": True}
