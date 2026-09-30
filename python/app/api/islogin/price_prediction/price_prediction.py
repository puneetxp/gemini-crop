from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.price_prediction import PricePrediction, PricePredictionInput
from app.services.price_prediction_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/price_prediction", tags=["islogin-price_prediction"])
service = get_service()

@router.get("/", response_model=List[PricePrediction])
def list_islogin_price_prediction(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=PricePrediction)
def show_islogin_price_prediction(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Price_prediction not found")
    return record
