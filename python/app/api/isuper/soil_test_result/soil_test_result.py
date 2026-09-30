from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.soil_test_result import SoilTestResult, SoilTestResultInput
from app.services.soil_test_result_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/soil_test_result", tags=["isuper-soil_test_result"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SoilTestResult])
def list_isuper_soil_test_result():
    return service.all()

@router.get("/{item_id}", response_model=SoilTestResult)
def show_isuper_soil_test_result(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Soil_test_result not found")
    return record

@router.post("/", response_model=SoilTestResult, status_code=201)
def create_isuper_soil_test_result(payload: SoilTestResultInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=SoilTestResult)
def update_isuper_soil_test_result(item_id: int, payload: SoilTestResultInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Soil_test_result not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_soil_test_result(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Soil_test_result not found")
    return {"success": True}
