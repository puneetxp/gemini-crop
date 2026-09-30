from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.supply_match import SupplyMatch, SupplyMatchInput
from app.services.supply_match_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/supply_match", tags=["isuper-supply_match"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SupplyMatch])
def list_isuper_supply_match():
    return service.all()

@router.get("/{item_id}", response_model=SupplyMatch)
def show_isuper_supply_match(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Supply_match not found")
    return record

@router.post("/", response_model=SupplyMatch, status_code=201)
def create_isuper_supply_match(payload: SupplyMatchInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=SupplyMatch)
def update_isuper_supply_match(item_id: int, payload: SupplyMatchInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Supply_match not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_supply_match(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Supply_match not found")
    return {"success": True}
