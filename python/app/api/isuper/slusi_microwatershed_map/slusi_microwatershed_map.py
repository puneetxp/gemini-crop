from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.slusi_microwatershed_map import SlusiMicrowatershedMap, SlusiMicrowatershedMapInput
from app.services.slusi_microwatershed_map_service import get_service
from app.core.auth import get_current_admin
from typing import List


router = APIRouter(prefix="/isuper/slusi_microwatershed_map", tags=["isuper-slusi_microwatershed_map"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SlusiMicrowatershedMap])
def list_isuper_slusi_microwatershed_map():
    return service.all()

@router.get("/{item_id}", response_model=SlusiMicrowatershedMap)
def show_isuper_slusi_microwatershed_map(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Slusi_microwatershed_map not found")
    return record
