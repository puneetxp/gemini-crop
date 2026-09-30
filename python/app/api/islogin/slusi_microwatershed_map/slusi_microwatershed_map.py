from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.slusi_microwatershed_map import SlusiMicrowatershedMap, SlusiMicrowatershedMapInput
from app.services.slusi_microwatershed_map_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/slusi_microwatershed_map", tags=["islogin-slusi_microwatershed_map"])
service = get_service()

@router.get("/", response_model=List[SlusiMicrowatershedMap])
def list_islogin_slusi_microwatershed_map(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=SlusiMicrowatershedMap)
def show_islogin_slusi_microwatershed_map(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Slusi_microwatershed_map not found")
    return record
