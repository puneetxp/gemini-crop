from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.quality_verification import QualityVerification, QualityVerificationInput
from app.services.quality_verification_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/quality_verification", tags=["isuper-quality_verification"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[QualityVerification])
def list_isuper_quality_verification():
    return service.all()

@router.get("/{item_id}", response_model=QualityVerification)
def show_isuper_quality_verification(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Quality_verification not found")
    return record

@router.post("/", response_model=QualityVerification, status_code=201)
def create_isuper_quality_verification(payload: QualityVerificationInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=QualityVerification)
def update_isuper_quality_verification(item_id: int, payload: QualityVerificationInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Quality_verification not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_quality_verification(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Quality_verification not found")
    return {"success": True}
