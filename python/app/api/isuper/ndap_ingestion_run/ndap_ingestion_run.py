from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.ndap_ingestion_run import NdapIngestionRun, NdapIngestionRunInput
from app.services.ndap_ingestion_run_service import get_service
from app.core.auth import get_current_admin
from typing import List


router = APIRouter(prefix="/isuper/ndap_ingestion_run", tags=["isuper-ndap_ingestion_run"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[NdapIngestionRun])
def list_isuper_ndap_ingestion_run():
    return service.all()

@router.get("/{item_id}", response_model=NdapIngestionRun)
def show_isuper_ndap_ingestion_run(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Ndap_ingestion_run not found")
    return record
