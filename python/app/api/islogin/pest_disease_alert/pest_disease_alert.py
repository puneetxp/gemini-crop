from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.pest_disease_alert import PestDiseaseAlert, PestDiseaseAlertInput
from app.services.pest_disease_alert_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/pest_disease_alert", tags=["islogin-pest_disease_alert"])
service = get_service()

@router.get("/", response_model=List[PestDiseaseAlert])
def list_islogin_pest_disease_alert(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=PestDiseaseAlert)
def show_islogin_pest_disease_alert(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Pest_disease_alert not found")
    return record

@router.post("/", response_model=PestDiseaseAlert, status_code=201)
def create_islogin_pest_disease_alert(payload: PestDiseaseAlertInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=PestDiseaseAlert)
def update_islogin_pest_disease_alert(item_id: int, payload: PestDiseaseAlertInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Pest_disease_alert not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_pest_disease_alert(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Pest_disease_alert not found")
    return {"success": True}
