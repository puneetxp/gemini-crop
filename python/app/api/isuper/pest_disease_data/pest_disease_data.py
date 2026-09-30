from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.pest_disease_data import PestDiseaseData, PestDiseaseDataInput
from app.services.pest_disease_data_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/pest_disease_data", tags=["isuper-pest_disease_data"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[PestDiseaseData])
def list_isuper_pest_disease_data():
    return service.all()

@router.get("/{item_id}", response_model=PestDiseaseData)
def show_isuper_pest_disease_data(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Pest_disease_data not found")
    return record

@router.post("/", response_model=PestDiseaseData, status_code=201)
def create_isuper_pest_disease_data(payload: PestDiseaseDataInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=PestDiseaseData)
def update_isuper_pest_disease_data(item_id: int, payload: PestDiseaseDataInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Pest_disease_data not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_pest_disease_data(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Pest_disease_data not found")
    return {"success": True}
