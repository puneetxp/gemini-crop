from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.historical_yield import HistoricalYield, HistoricalYieldInput
from app.services.historical_yield_service import get_service
from typing import List


router = APIRouter(prefix="/ipublic/historical_yield", tags=["ipublic-historical_yield"])
service = get_service()

@router.get("/", response_model=List[HistoricalYield])
def list_ipublic_historical_yield():
    return service.all()

@router.get("/{item_id}", response_model=HistoricalYield)
def show_ipublic_historical_yield(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Historical_yield not found")
    return record
