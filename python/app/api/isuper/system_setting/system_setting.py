from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.system_setting import SystemSetting, SystemSettingInput
from app.services.system_setting_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/system_setting", tags=["isuper-system_setting"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SystemSetting])
def list_isuper_system_setting():
    return service.all()

@router.get("/{item_id}", response_model=SystemSetting)
def show_isuper_system_setting(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="System_setting not found")
    return record

@router.post("/", response_model=SystemSetting, status_code=201)
def create_isuper_system_setting(payload: SystemSettingInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=SystemSetting)
def update_isuper_system_setting(item_id: int, payload: SystemSettingInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="System_setting not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_system_setting(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="System_setting not found")
    return {"success": True}
