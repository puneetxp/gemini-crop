from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.seasonal_trend import SeasonalTrend, SeasonalTrendInput
from app.services.seasonal_trend_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/seasonal_trend", tags=["islogin-seasonal_trend"])
service = get_service()

@router.get("/", response_model=List[SeasonalTrend])
def list_islogin_seasonal_trend(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=SeasonalTrend)
def show_islogin_seasonal_trend(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Seasonal_trend not found")
    return record
