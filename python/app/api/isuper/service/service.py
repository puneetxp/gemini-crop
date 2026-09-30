from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.service import Service, ServiceInput
from app.services.service_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/service", tags=["isuper-service"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[Service])
def list_isuper_service():
    return service.all()

@router.get("/{item_id}", response_model=Service)
def show_isuper_service(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Service not found")
    return record

@router.post("/", response_model=Service, status_code=201)
def create_isuper_service(payload: ServiceInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=Service)
def update_isuper_service(item_id: int, payload: ServiceInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_service(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": True}
