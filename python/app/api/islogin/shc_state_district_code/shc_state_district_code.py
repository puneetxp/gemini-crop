from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.shc_state_district_code import ShcStateDistrictCode, ShcStateDistrictCodeInput
from app.services.shc_state_district_code_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/shc_state_district_code", tags=["islogin-shc_state_district_code"])
service = get_service()

@router.get("/", response_model=List[ShcStateDistrictCode])
def list_islogin_shc_state_district_code(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=ShcStateDistrictCode)
def show_islogin_shc_state_district_code(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Shc_state_district_code not found")
    return record
