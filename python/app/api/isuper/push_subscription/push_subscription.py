from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.push_subscription import PushSubscription, PushSubscriptionInput
from app.services.push_subscription_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/push_subscription", tags=["isuper-push_subscription"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[PushSubscription])
def list_isuper_push_subscription():
    return service.all()

@router.get("/{item_id}", response_model=PushSubscription)
def show_isuper_push_subscription(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Push_subscription not found")
    return record

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_push_subscription(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Push_subscription not found")
    return {"success": True}
