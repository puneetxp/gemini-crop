from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.slusi_lcc_report import SlusiLccReport, SlusiLccReportInput
from app.services.slusi_lcc_report_service import get_service
from app.core.auth import get_current_admin
from typing import List


router = APIRouter(prefix="/isuper/slusi_lcc_report", tags=["isuper-slusi_lcc_report"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SlusiLccReport])
def list_isuper_slusi_lcc_report():
    return service.all()

@router.get("/{item_id}", response_model=SlusiLccReport)
def show_isuper_slusi_lcc_report(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Slusi_lcc_report not found")
    return record
