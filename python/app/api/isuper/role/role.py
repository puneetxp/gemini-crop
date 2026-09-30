from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.role import Role, RoleInput
from app.services.role_service import get_service
from app.core.auth import get_current_admin
from typing import List


router = APIRouter(prefix="/isuper/role", tags=["isuper-role"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[Role])
def list_isuper_role():
    return service.all()

@router.get("/{item_id}", response_model=Role)
def show_isuper_role(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Role not found")
    return record

@router.post("/", response_model=Role, status_code=201)
def create_isuper_role(payload: RoleInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=Role)
def update_isuper_role(item_id: int, payload: RoleInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Role not found")
    return updated

@router.post("/upsert", response_model=Role)
def upsert_isuper_role(payload: RoleInput):
    return service.upsert(payload.dict(exclude_unset=True))
