from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.livestock_listing import LivestockListing, LivestockListingInput
from app.services.livestock_listing_service import get_service


router = APIRouter(prefix="/ipublic/livestock_listing", tags=["ipublic-livestock_listing"])
service = get_service()

@router.get("/{item_id}", response_model=LivestockListing)
def show_ipublic_livestock_listing(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock_listing not found")
    return record
