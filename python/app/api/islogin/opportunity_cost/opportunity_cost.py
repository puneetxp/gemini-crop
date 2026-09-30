from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.opportunity_cost import OpportunityCost, OpportunityCostInput
from app.services.opportunity_cost_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/opportunity_cost", tags=["islogin-opportunity_cost"])
service = get_service()

@router.get("/", response_model=List[OpportunityCost])
def list_islogin_opportunity_cost(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=OpportunityCost)
def show_islogin_opportunity_cost(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Opportunity_cost not found")
    return record
