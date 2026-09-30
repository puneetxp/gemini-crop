from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.supply_request import SupplyRequest, SupplyRequestInput
from app.services.supply_request_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/supply_request", tags=["isuper-supply_request"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SupplyRequest])
def list_isuper_supply_request():
    return service.all()

@router.get("/{item_id}", response_model=SupplyRequest)
def show_isuper_supply_request(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Supply_request not found")
    return record

@router.post("/", response_model=SupplyRequest, status_code=201)
def create_isuper_supply_request(payload: SupplyRequestInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=SupplyRequest)
def update_isuper_supply_request(item_id: int, payload: SupplyRequestInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Supply_request not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_supply_request(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Supply_request not found")
    return {"success": True}
