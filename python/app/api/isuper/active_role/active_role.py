from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.active_role import ActiveRole, ActiveRoleInput
from app.services.active_role_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/active_role", tags=["isuper-active_role"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[ActiveRole])
def list_isuper_active_role():
    return service.all()

@router.get("/{item_id}", response_model=ActiveRole)
def show_isuper_active_role(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Active_role not found")
    return record

@router.post("/", response_model=ActiveRole, status_code=201)
def create_isuper_active_role(payload: ActiveRoleInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=ActiveRole)
def update_isuper_active_role(item_id: int, payload: ActiveRoleInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Active_role not found")
    return updated

@router.post("/upsert", response_model=ActiveRole)
def upsert_isuper_active_role(payload: ActiveRoleInput):
    return service.upsert(payload.dict(exclude_unset=True))

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_active_role(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Active_role not found")
    return {"success": True}
