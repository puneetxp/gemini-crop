from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.msp_rate import MspRate, MspRateInput
from app.services.msp_rate_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/msp_rate", tags=["islogin-msp_rate"])
service = get_service()

@router.get("/", response_model=List[MspRate])
def list_islogin_msp_rate(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=MspRate)
def show_islogin_msp_rate(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Msp_rate not found")
    return record
