from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.livestock_listing import LivestockListing, LivestockListingInput
from app.services.livestock_listing_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/livestock_listing", tags=["isuper-livestock_listing"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[LivestockListing])
def list_isuper_livestock_listing():
    return service.all()

@router.get("/{item_id}", response_model=LivestockListing)
def show_isuper_livestock_listing(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Livestock_listing not found")
    return record

@router.post("/", response_model=LivestockListing, status_code=201)
def create_isuper_livestock_listing(payload: LivestockListingInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=LivestockListing)
def update_isuper_livestock_listing(item_id: int, payload: LivestockListingInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Livestock_listing not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_livestock_listing(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Livestock_listing not found")
    return {"success": True}
