from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.active_role import ActiveRole, ActiveRoleInput
from app.services.active_role_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/active_role", tags=["islogin-active_role"])
service = get_service()

@router.get("/", response_model=List[ActiveRole])
def list_islogin_active_role(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=ActiveRole)
def show_islogin_active_role(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Active_role not found")
    return record
