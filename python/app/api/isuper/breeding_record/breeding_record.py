from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.breeding_record import BreedingRecord, BreedingRecordInput
from app.services.breeding_record_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/breeding_record", tags=["isuper-breeding_record"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[BreedingRecord])
def list_isuper_breeding_record():
    return service.all()

@router.get("/{item_id}", response_model=BreedingRecord)
def show_isuper_breeding_record(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Breeding_record not found")
    return record

@router.post("/", response_model=BreedingRecord, status_code=201)
def create_isuper_breeding_record(payload: BreedingRecordInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=BreedingRecord)
def update_isuper_breeding_record(item_id: int, payload: BreedingRecordInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Breeding_record not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_breeding_record(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Breeding_record not found")
    return {"success": True}
