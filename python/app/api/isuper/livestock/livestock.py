from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.livestock import Livestock, LivestockInput
from app.services.livestock_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/livestock", tags=["isuper-livestock"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[Livestock])
def list_isuper_livestock():
    return service.all()

@router.get("/{item_id}", response_model=Livestock)
def show_isuper_livestock(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock not found")
    return record

@router.post("/", response_model=Livestock, status_code=201)
def create_isuper_livestock(payload: LivestockInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=Livestock)
def update_isuper_livestock(item_id: int, payload: LivestockInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Livestock not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_livestock(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Livestock not found")
    return {"success": True}
