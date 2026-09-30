from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.advance_booking import AdvanceBooking, AdvanceBookingInput
from app.services.advance_booking_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/advance_booking", tags=["isuper-advance_booking"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[AdvanceBooking])
def list_isuper_advance_booking():
    return service.all()

@router.get("/{item_id}", response_model=AdvanceBooking)
def show_isuper_advance_booking(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Advance_booking not found")
    return record

@router.post("/", response_model=AdvanceBooking, status_code=201)
def create_isuper_advance_booking(payload: AdvanceBookingInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=AdvanceBooking)
def update_isuper_advance_booking(item_id: int, payload: AdvanceBookingInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Advance_booking not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_advance_booking(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Advance_booking not found")
    return {"success": True}
