from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.user import User, UserInput
from app.services.user_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/user", tags=["islogin-user"])
service = get_service()

@router.get("/", response_model=List[User])
def list_islogin_user(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=User)
def show_islogin_user(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="User not found")
    return record

@router.put("/{item_id}", response_model=User)
def update_islogin_user(item_id: int, payload: UserInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated
