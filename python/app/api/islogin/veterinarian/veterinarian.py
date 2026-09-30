from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.veterinarian import Veterinarian, VeterinarianInput
from app.services.veterinarian_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/veterinarian", tags=["islogin-veterinarian"])
service = get_service()

@router.get("/", response_model=List[Veterinarian])
def list_islogin_veterinarian(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=Veterinarian)
def show_islogin_veterinarian(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return record

@router.post("/", response_model=Veterinarian, status_code=201)
def create_islogin_veterinarian(payload: VeterinarianInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=Veterinarian)
def update_islogin_veterinarian(item_id: int, payload: VeterinarianInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_veterinarian(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return {"success": True}
