from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.annual_strategy import AnnualStrategy, AnnualStrategyInput
from app.services.annual_strategy_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/annual_strategy", tags=["isuper-annual_strategy"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[AnnualStrategy])
def list_isuper_annual_strategy():
    return service.all()

@router.get("/{item_id}", response_model=AnnualStrategy)
def show_isuper_annual_strategy(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Annual_strategy not found")
    return record

@router.post("/", response_model=AnnualStrategy, status_code=201)
def create_isuper_annual_strategy(payload: AnnualStrategyInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=AnnualStrategy)
def update_isuper_annual_strategy(item_id: int, payload: AnnualStrategyInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Annual_strategy not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_annual_strategy(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Annual_strategy not found")
    return {"success": True}
