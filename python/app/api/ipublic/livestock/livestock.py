from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.livestock import Livestock
from app.services.livestock_service import get_service


router = APIRouter(prefix="/ipublic/livestock", tags=["ipublic-livestock"])
service = get_service()

@router.get("/{item_id}", response_model=Livestock)
def show_ipublic_livestock(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock not found")
    return record
