from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.livestock_marketplace_listing import LivestockMarketplaceListing, LivestockMarketplaceListingInput
from app.services.livestock_marketplace_listing_service import get_service
from app.core.auth import get_current_active_user
from typing import List, Dict


router = APIRouter(prefix="/islogin/livestock_marketplace_listing", tags=["islogin-livestock_marketplace_listing"])
service = get_service()

@router.get("/", response_model=List[LivestockMarketplaceListing])
def list_islogin_livestock_marketplace_listing(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=LivestockMarketplaceListing)
def show_islogin_livestock_marketplace_listing(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock_marketplace_listing not found")
    return record

@router.post("/", response_model=LivestockMarketplaceListing, status_code=201)
def create_islogin_livestock_marketplace_listing(payload: LivestockMarketplaceListingInput, current_user=Depends(get_current_active_user)):
    return service.create(payload.dict(exclude_unset=True), owner=current_user)

@router.put("/{item_id}", response_model=LivestockMarketplaceListing)
def update_islogin_livestock_marketplace_listing(item_id: int, payload: LivestockMarketplaceListingInput, current_user=Depends(get_current_active_user)):
    updated = service.update(item_id, payload.dict(exclude_unset=True), owner=current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Livestock_marketplace_listing not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_islogin_livestock_marketplace_listing(item_id: int, current_user=Depends(get_current_active_user)):
    if not service.delete(item_id, owner=current_user):
        raise HTTPException(status_code=404, detail="Livestock_marketplace_listing not found")
    return {"success": True}
