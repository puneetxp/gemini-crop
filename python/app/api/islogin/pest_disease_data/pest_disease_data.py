from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.pest_disease_data import PestDiseaseData, PestDiseaseDataInput
from app.services.pest_disease_data_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/pest_disease_data", tags=["islogin-pest_disease_data"])
service = get_service()

@router.get("/", response_model=List[PestDiseaseData])
def list_islogin_pest_disease_data(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=PestDiseaseData)
def show_islogin_pest_disease_data(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Pest_disease_data not found")
    return record
