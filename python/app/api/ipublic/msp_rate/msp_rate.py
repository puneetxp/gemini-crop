from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.msp_rate import MspRate, MspRateInput
from app.services.msp_rate_service import get_service


router = APIRouter(prefix="/ipublic/msp_rate", tags=["ipublic-msp_rate"])
service = get_service()

@router.get("/{item_id}", response_model=MspRate)
def show_ipublic_msp_rate(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Msp_rate not found")
    return record
