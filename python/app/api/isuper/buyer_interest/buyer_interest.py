from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.buyer_interest import BuyerInterest, BuyerInterestInput
from app.services.buyer_interest_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/buyer_interest", tags=["isuper-buyer_interest"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[BuyerInterest])
def list_isuper_buyer_interest():
    return service.all()

@router.get("/{item_id}", response_model=BuyerInterest)
def show_isuper_buyer_interest(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Buyer_interest not found")
    return record

@router.post("/", response_model=BuyerInterest, status_code=201)
def create_isuper_buyer_interest(payload: BuyerInterestInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=BuyerInterest)
def update_isuper_buyer_interest(item_id: int, payload: BuyerInterestInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Buyer_interest not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_buyer_interest(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Buyer_interest not found")
    return {"success": True}
