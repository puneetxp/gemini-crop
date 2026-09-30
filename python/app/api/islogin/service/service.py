from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.service import Service, ServiceInput
from app.services.service_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/service", tags=["islogin-service"])
service = get_service()

@router.get("/", response_model=List[Service])
def list_islogin_service(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=Service)
def show_islogin_service(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Service not found")
    return record
