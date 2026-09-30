from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.slusi_lcc_report import SlusiLccReport, SlusiLccReportInput
from app.services.slusi_lcc_report_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/slusi_lcc_report", tags=["islogin-slusi_lcc_report"])
service = get_service()

@router.get("/", response_model=List[SlusiLccReport])
def list_islogin_slusi_lcc_report(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=SlusiLccReport)
def show_islogin_slusi_lcc_report(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Slusi_lcc_report not found")
    return record
