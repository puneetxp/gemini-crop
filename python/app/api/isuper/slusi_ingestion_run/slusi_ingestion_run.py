from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.slusi_ingestion_run import SlusiIngestionRun, SlusiIngestionRunInput
from app.services.slusi_ingestion_run_service import get_service
from app.core.auth import get_current_admin
from typing import List


router = APIRouter(prefix="/isuper/slusi_ingestion_run", tags=["isuper-slusi_ingestion_run"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[SlusiIngestionRun])
def list_isuper_slusi_ingestion_run():
    return service.all()

@router.get("/{item_id}", response_model=SlusiIngestionRun)
def show_isuper_slusi_ingestion_run(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Slusi_ingestion_run not found")
    return record
