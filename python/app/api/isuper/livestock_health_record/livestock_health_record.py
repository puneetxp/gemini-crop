from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.livestock_health_record import LivestockHealthRecord, LivestockHealthRecordInput
from app.services.livestock_health_record_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/livestock_health_record", tags=["isuper-livestock_health_record"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[LivestockHealthRecord])
def list_isuper_livestock_health_record():
    return service.all()

@router.get("/{item_id}", response_model=LivestockHealthRecord)
def show_isuper_livestock_health_record(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock_health_record not found")
    return record

@router.post("/", response_model=LivestockHealthRecord, status_code=201)
def create_isuper_livestock_health_record(payload: LivestockHealthRecordInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=LivestockHealthRecord)
def update_isuper_livestock_health_record(item_id: int, payload: LivestockHealthRecordInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Livestock_health_record not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_livestock_health_record(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Livestock_health_record not found")
    return {"success": True}
