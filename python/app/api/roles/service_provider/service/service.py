from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.service import Service, ServiceInput
from app.services.service_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/service_provider/service", tags=["service_provider-service"])
service = get_service()

@router.get("/", response_model=List[Service])
def list_service_provider_service(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=Service)
def show_service_provider_service(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Service not found")
    return record

@router.post("/", response_model=Service, status_code=201)
def create_service_provider_service(payload: ServiceInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=Service)
def update_service_provider_service(item_id: int, payload: ServiceInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_service_provider_service(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": True}
