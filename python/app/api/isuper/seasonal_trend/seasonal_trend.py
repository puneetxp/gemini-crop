from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.seasonal_trend import SeasonalTrend, SeasonalTrendInput
from app.services.seasonal_trend_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/seasonal_trend", tags=["isuper-seasonal_trend"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SeasonalTrend])
def list_isuper_seasonal_trend():
    return service.all()

@router.get("/{item_id}", response_model=SeasonalTrend)
def show_isuper_seasonal_trend(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Seasonal_trend not found")
    return record

@router.post("/", response_model=SeasonalTrend, status_code=201)
def create_isuper_seasonal_trend(payload: SeasonalTrendInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=SeasonalTrend)
def update_isuper_seasonal_trend(item_id: int, payload: SeasonalTrendInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Seasonal_trend not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_seasonal_trend(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Seasonal_trend not found")
    return {"success": True}
