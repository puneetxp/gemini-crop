from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.pest_disease_alert import PestDiseaseAlert, PestDiseaseAlertInput
from app.services.pest_disease_alert_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/pest_disease_alert", tags=["isuper-pest_disease_alert"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[PestDiseaseAlert])
def list_isuper_pest_disease_alert():
    return service.all()

@router.get("/{item_id}", response_model=PestDiseaseAlert)
def show_isuper_pest_disease_alert(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pest_disease_alert not found")
    return record

@router.post("/", response_model=PestDiseaseAlert, status_code=201)
def create_isuper_pest_disease_alert(payload: PestDiseaseAlertInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=PestDiseaseAlert)
def update_isuper_pest_disease_alert(item_id: int, payload: PestDiseaseAlertInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Pest_disease_alert not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_pest_disease_alert(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Pest_disease_alert not found")
    return {"success": True}
