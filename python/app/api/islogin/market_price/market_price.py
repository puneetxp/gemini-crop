from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.market_price import MarketPrice, MarketPriceInput
from app.services.market_price_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/market_price", tags=["islogin-market_price"])
service = get_service()

@router.get("/", response_model=List[MarketPrice])
def list_islogin_market_price(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=MarketPrice)
def show_islogin_market_price(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Market_price not found")
    return record
