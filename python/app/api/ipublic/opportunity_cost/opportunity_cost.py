from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.opportunity_cost import OpportunityCost, OpportunityCostInput
from app.services.opportunity_cost_service import get_service
from typing import List


router = APIRouter(prefix="/ipublic/opportunity_cost", tags=["ipublic-opportunity_cost"])
service = get_service()

@router.get("/", response_model=List[OpportunityCost])
def list_ipublic_opportunity_cost():
    return service.all()

@router.get("/{item_id}", response_model=OpportunityCost)
def show_ipublic_opportunity_cost(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Opportunity_cost not found")
    return record
