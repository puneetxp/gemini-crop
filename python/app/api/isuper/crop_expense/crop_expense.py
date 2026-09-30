from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.crop_expense import CropExpense, CropExpenseInput
from app.services.crop_expense_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/crop_expense", tags=["isuper-crop_expense"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[CropExpense])
def list_isuper_crop_expense():
    return service.all()

@router.get("/{item_id}", response_model=CropExpense)
def show_isuper_crop_expense(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Crop_expense not found")
    return record

@router.post("/", response_model=CropExpense, status_code=201)
def create_isuper_crop_expense(payload: CropExpenseInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=CropExpense)
def update_isuper_crop_expense(item_id: int, payload: CropExpenseInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Crop_expense not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_crop_expense(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Crop_expense not found")
    return {"success": True}
