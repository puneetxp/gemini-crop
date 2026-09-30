from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.shc_state_district_code import ShcStateDistrictCode, ShcStateDistrictCodeInput
from app.services.shc_state_district_code_service import get_service
from app.core.auth import get_current_admin
from typing import List


router = APIRouter(prefix="/isuper/shc_state_district_code", tags=["isuper-shc_state_district_code"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[ShcStateDistrictCode])
def list_isuper_shc_state_district_code():
    return service.all()

@router.get("/{item_id}", response_model=ShcStateDistrictCode)
def show_isuper_shc_state_district_code(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Shc_state_district_code not found")
    return record
