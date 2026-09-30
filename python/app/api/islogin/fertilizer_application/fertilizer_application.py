from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.fertilizer_application import FertilizerApplication, FertilizerApplicationInput
from app.services.fertilizer_application_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/fertilizer_application", tags=["islogin-fertilizer_application"])
service = get_service()

@router.get("/", response_model=List[FertilizerApplication])
def list_islogin_fertilizer_application(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=FertilizerApplication)
def show_islogin_fertilizer_application(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Fertilizer_application not found")
    return record

@router.post("/", response_model=FertilizerApplication, status_code=201)
def create_islogin_fertilizer_application(payload: FertilizerApplicationInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=FertilizerApplication)
def update_islogin_fertilizer_application(item_id: int, payload: FertilizerApplicationInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Fertilizer_application not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_fertilizer_application(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Fertilizer_application not found")
    return {"success": True}
