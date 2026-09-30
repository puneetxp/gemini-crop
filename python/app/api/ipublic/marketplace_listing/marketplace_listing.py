from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.models.marketplace_listing import MarketplaceListing, MarketplaceListingInput
from app.services.marketplace_listing_service import get_service


router = APIRouter(prefix="/ipublic/marketplace_listing", tags=["ipublic-marketplace_listing"])
service = get_service()

@router.get("/{item_id}", response_model=MarketplaceListing)
def show_ipublic_marketplace_listing(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Marketplace_listing not found")
    return record
