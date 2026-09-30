from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.seasonal_trend import SeasonalTrend, SeasonalTrendInput
from app.services.seasonal_trend_service import get_service
from typing import List


router = APIRouter(prefix="/ipublic/seasonal_trend", tags=["ipublic-seasonal_trend"])
service = get_service()

@router.get("/", response_model=List[SeasonalTrend])
def list_ipublic_seasonal_trend():
    return service.all()

@router.get("/{item_id}", response_model=SeasonalTrend)
def show_ipublic_seasonal_trend(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Seasonal_trend not found")
    return record
