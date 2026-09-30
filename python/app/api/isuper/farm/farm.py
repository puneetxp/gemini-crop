from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.farm import Farm, FarmInput
from app.services.farm_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/farm", tags=["isuper-farm"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[Farm])
def list_isuper_farm():
    return service.all()

@router.get("/{item_id}", response_model=Farm)
def show_isuper_farm(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Farm not found")
    return record

@router.post("/", response_model=Farm, status_code=201)
def create_isuper_farm(payload: FarmInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=Farm)
def update_isuper_farm(item_id: int, payload: FarmInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Farm not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_farm(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Farm not found")
    return {"success": True}
