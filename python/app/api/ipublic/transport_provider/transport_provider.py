from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.transport_provider import TransportProvider, TransportProviderInput
from app.services.transport_provider_service import get_service


router = APIRouter(prefix="/ipublic/transport_provider", tags=["ipublic-transport_provider"])
service = get_service()

@router.get("/{item_id}", response_model=TransportProvider)
def show_ipublic_transport_provider(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Transport_provider not found")
    return record
