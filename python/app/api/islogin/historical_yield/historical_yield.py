from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.historical_yield import HistoricalYield, HistoricalYieldInput
from app.services.historical_yield_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/historical_yield", tags=["islogin-historical_yield"])
service = get_service()

@router.get("/", response_model=List[HistoricalYield])
def list_islogin_historical_yield(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=HistoricalYield)
def show_islogin_historical_yield(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Historical_yield not found")
    return record
