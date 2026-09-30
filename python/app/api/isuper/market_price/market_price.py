from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.market_price import MarketPrice, MarketPriceInput
from app.services.market_price_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/market_price", tags=["isuper-market_price"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[MarketPrice])
def list_isuper_market_price():
    return service.all()

@router.get("/{item_id}", response_model=MarketPrice)
def show_isuper_market_price(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Market_price not found")
    return record

@router.post("/", response_model=MarketPrice, status_code=201)
def create_isuper_market_price(payload: MarketPriceInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=MarketPrice)
def update_isuper_market_price(item_id: int, payload: MarketPriceInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Market_price not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_market_price(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Market_price not found")
    return {"success": True}
