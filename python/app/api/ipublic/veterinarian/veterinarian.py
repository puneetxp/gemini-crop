from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.veterinarian import Veterinarian, VeterinarianInput
from app.services.veterinarian_service import get_service
from typing import List


router = APIRouter(prefix="/ipublic/veterinarian", tags=["ipublic-veterinarian"])
service = get_service()

@router.get("/", response_model=List[Veterinarian])
def list_ipublic_veterinarian():
    return service.all()

@router.get("/{item_id}", response_model=Veterinarian)
def show_ipublic_veterinarian(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return record
