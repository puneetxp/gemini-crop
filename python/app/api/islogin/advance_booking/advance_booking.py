from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.advance_booking import AdvanceBooking, AdvanceBookingInput
from app.services.advance_booking_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/advance_booking", tags=["islogin-advance_booking"])
service = get_service()

@router.get("/", response_model=List[AdvanceBooking])
def list_islogin_advance_booking(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=AdvanceBooking)
def show_islogin_advance_booking(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Advance_booking not found")
    return record

@router.post("/", response_model=AdvanceBooking, status_code=201)
def create_islogin_advance_booking(payload: AdvanceBookingInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=AdvanceBooking)
def update_islogin_advance_booking(item_id: int, payload: AdvanceBookingInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Advance_booking not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_advance_booking(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Advance_booking not found")
    return {"success": True}
