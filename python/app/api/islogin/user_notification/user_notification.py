from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.user_notification import UserNotification, UserNotificationInput
from app.services.user_notification_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/user_notification", tags=["islogin-user_notification"])
service = get_service()

@router.get("/", response_model=List[UserNotification])
def list_islogin_user_notification(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=UserNotification)
def show_islogin_user_notification(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="User_notification not found")
    return record

@router.put("/{item_id}", response_model=UserNotification)
def update_islogin_user_notification(item_id: int, payload: UserNotificationInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="User_notification not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_user_notification(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="User_notification not found")
    return {"success": True}
