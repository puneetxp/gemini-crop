from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.veterinarian import Veterinarian, VeterinarianInput
from app.services.veterinarian_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/veterinarian", tags=["isuper-veterinarian"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[Veterinarian])
def list_isuper_veterinarian():
    return service.all()

@router.get("/{item_id}", response_model=Veterinarian)
def show_isuper_veterinarian(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return record

@router.post("/", response_model=Veterinarian, status_code=201)
def create_isuper_veterinarian(payload: VeterinarianInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=Veterinarian)
def update_isuper_veterinarian(item_id: int, payload: VeterinarianInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_veterinarian(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return {"success": True}
