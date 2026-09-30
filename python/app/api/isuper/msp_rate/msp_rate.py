from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.msp_rate import MspRate, MspRateInput
from app.services.msp_rate_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/msp_rate", tags=["isuper-msp_rate"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[MspRate])
def list_isuper_msp_rate():
    return service.all()

@router.get("/{item_id}", response_model=MspRate)
def show_isuper_msp_rate(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Msp_rate not found")
    return record

@router.post("/", response_model=MspRate, status_code=201)
def create_isuper_msp_rate(payload: MspRateInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=MspRate)
def update_isuper_msp_rate(item_id: int, payload: MspRateInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Msp_rate not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_msp_rate(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Msp_rate not found")
    return {"success": True}
