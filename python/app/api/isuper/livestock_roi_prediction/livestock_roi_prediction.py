from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.livestock_roi_prediction import LivestockRoiPrediction, LivestockRoiPredictionInput
from app.services.livestock_roi_prediction_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/livestock_roi_prediction", tags=["isuper-livestock_roi_prediction"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[LivestockRoiPrediction])
def list_isuper_livestock_roi_prediction():
    return service.all()

@router.get("/{item_id}", response_model=LivestockRoiPrediction)
def show_isuper_livestock_roi_prediction(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock_roi_prediction not found")
    return record

@router.post("/", response_model=LivestockRoiPrediction, status_code=201)
def create_isuper_livestock_roi_prediction(payload: LivestockRoiPredictionInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=LivestockRoiPrediction)
def update_isuper_livestock_roi_prediction(item_id: int, payload: LivestockRoiPredictionInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Livestock_roi_prediction not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_livestock_roi_prediction(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Livestock_roi_prediction not found")
    return {"success": True}
