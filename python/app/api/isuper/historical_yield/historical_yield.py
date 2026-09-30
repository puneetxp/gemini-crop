from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.historical_yield import HistoricalYield, HistoricalYieldInput
from app.services.historical_yield_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/historical_yield", tags=["isuper-historical_yield"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[HistoricalYield])
def list_isuper_historical_yield():
    return service.all()

@router.get("/{item_id}", response_model=HistoricalYield)
def show_isuper_historical_yield(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Historical_yield not found")
    return record

@router.post("/", response_model=HistoricalYield, status_code=201)
def create_isuper_historical_yield(payload: HistoricalYieldInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=HistoricalYield)
def update_isuper_historical_yield(item_id: int, payload: HistoricalYieldInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Historical_yield not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_historical_yield(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Historical_yield not found")
    return {"success": True}
