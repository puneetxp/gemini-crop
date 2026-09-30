from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop_diagnosis import CropDiagnosis, CropDiagnosisInput
from app.services.crop_diagnosis_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/crop_diagnosis", tags=["isuper-crop_diagnosis"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[CropDiagnosis])
def list_isuper_crop_diagnosis():
    return service.all()

@router.get("/{item_id}", response_model=CropDiagnosis)
def show_isuper_crop_diagnosis(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_diagnosis not found")
    return record

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_crop_diagnosis(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Crop_diagnosis not found")
    return {"success": True}
