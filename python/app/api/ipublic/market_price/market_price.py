from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.market_price import MarketPrice, MarketPriceInput
from app.services.market_price_service import get_service


router = APIRouter(prefix="/ipublic/market_price", tags=["ipublic-market_price"])
service = get_service()

@router.get("/{item_id}", response_model=MarketPrice)
def show_ipublic_market_price(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Market_price not found")
    return record
