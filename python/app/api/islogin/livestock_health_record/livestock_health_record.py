from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.livestock_health_record import LivestockHealthRecord, LivestockHealthRecordInput
from app.services.livestock_health_record_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/livestock_health_record", tags=["islogin-livestock_health_record"])
service = get_service()

@router.get("/", response_model=List[LivestockHealthRecord])
def list_islogin_livestock_health_record(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=LivestockHealthRecord)
def show_islogin_livestock_health_record(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock_health_record not found")
    return record

@router.post("/", response_model=LivestockHealthRecord, status_code=201)
def create_islogin_livestock_health_record(payload: LivestockHealthRecordInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=LivestockHealthRecord)
def update_islogin_livestock_health_record(item_id: int, payload: LivestockHealthRecordInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Livestock_health_record not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_livestock_health_record(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Livestock_health_record not found")
    return {"success": True}
