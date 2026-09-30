from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.opportunity_cost import OpportunityCost, OpportunityCostInput
from app.services.opportunity_cost_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/opportunity_cost", tags=["isuper-opportunity_cost"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[OpportunityCost])
def list_isuper_opportunity_cost():
    return service.all()

@router.get("/{item_id}", response_model=OpportunityCost)
def show_isuper_opportunity_cost(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Opportunity_cost not found")
    return record

@router.post("/", response_model=OpportunityCost, status_code=201)
def create_isuper_opportunity_cost(payload: OpportunityCostInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=OpportunityCost)
def update_isuper_opportunity_cost(item_id: int, payload: OpportunityCostInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Opportunity_cost not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_opportunity_cost(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Opportunity_cost not found")
    return {"success": True}
