from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop_diagnosis import CropDiagnosis, CropDiagnosisInput
from app.services.crop_diagnosis_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/crop_diagnosis", tags=["islogin-crop_diagnosis"])
service = get_service()

@router.get("/", response_model=List[CropDiagnosis])
def list_islogin_crop_diagnosis(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=CropDiagnosis)
def show_islogin_crop_diagnosis(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_diagnosis not found")
    return record

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_crop_diagnosis(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Crop_diagnosis not found")
    return {"success": True}
