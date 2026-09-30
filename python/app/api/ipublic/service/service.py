from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.service import Service, ServiceInput
from app.services.service_service import get_service
from typing import List


router = APIRouter(prefix="/ipublic/service", tags=["ipublic-service"])
service = get_service()

@router.get("/", response_model=List[Service])
def list_ipublic_service():
    return service.all()

@router.get("/{item_id}", response_model=Service)
def show_ipublic_service(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Service not found")
    return record
