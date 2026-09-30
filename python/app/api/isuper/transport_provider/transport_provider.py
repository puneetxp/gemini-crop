from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.transport_provider import TransportProvider, TransportProviderInput
from app.services.transport_provider_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/transport_provider", tags=["isuper-transport_provider"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[TransportProvider])
def list_isuper_transport_provider():
    return service.all()

@router.get("/{item_id}", response_model=TransportProvider)
def show_isuper_transport_provider(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transport_provider not found")
    return record

@router.post("/", response_model=TransportProvider, status_code=201)
def create_isuper_transport_provider(payload: TransportProviderInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=TransportProvider)
def update_isuper_transport_provider(item_id: int, payload: TransportProviderInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Transport_provider not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_transport_provider(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Transport_provider not found")
    return {"success": True}
