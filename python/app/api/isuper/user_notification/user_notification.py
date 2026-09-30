from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.user_notification import UserNotification, UserNotificationInput
from app.services.user_notification_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/user_notification", tags=["isuper-user_notification"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[UserNotification])
def list_isuper_user_notification():
    return service.all()

@router.get("/{item_id}", response_model=UserNotification)
def show_isuper_user_notification(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="User_notification not found")
    return record

@router.post("/", response_model=UserNotification, status_code=201)
def create_isuper_user_notification(payload: UserNotificationInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=UserNotification)
def update_isuper_user_notification(item_id: int, payload: UserNotificationInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="User_notification not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_user_notification(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="User_notification not found")
    return {"success": True}
