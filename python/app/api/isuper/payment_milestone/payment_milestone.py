from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.payment_milestone import PaymentMilestone, PaymentMilestoneInput
from app.services.payment_milestone_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/payment_milestone", tags=["isuper-payment_milestone"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[PaymentMilestone])
def list_isuper_payment_milestone():
    return service.all()

@router.get("/{item_id}", response_model=PaymentMilestone)
def show_isuper_payment_milestone(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payment_milestone not found")
    return record

@router.post("/", response_model=PaymentMilestone, status_code=201)
def create_isuper_payment_milestone(payload: PaymentMilestoneInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=PaymentMilestone)
def update_isuper_payment_milestone(item_id: int, payload: PaymentMilestoneInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Payment_milestone not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_payment_milestone(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Payment_milestone not found")
    return {"success": True}
