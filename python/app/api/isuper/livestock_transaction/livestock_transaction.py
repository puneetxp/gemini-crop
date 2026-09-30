from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.livestock_transaction import LivestockTransaction, LivestockTransactionInput
from app.services.livestock_transaction_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/livestock_transaction", tags=["isuper-livestock_transaction"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[LivestockTransaction])
def list_isuper_livestock_transaction():
    return service.all()

@router.get("/{item_id}", response_model=LivestockTransaction)
def show_isuper_livestock_transaction(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock_transaction not found")
    return record

@router.post("/", response_model=LivestockTransaction, status_code=201)
def create_isuper_livestock_transaction(payload: LivestockTransactionInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=LivestockTransaction)
def update_isuper_livestock_transaction(item_id: int, payload: LivestockTransactionInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Livestock_transaction not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_livestock_transaction(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Livestock_transaction not found")
    return {"success": True}
