from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.offspring import Offspring, OffspringInput
from app.services.offspring_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/offspring", tags=["isuper-offspring"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[Offspring])
def list_isuper_offspring():
    return service.all()

@router.get("/{item_id}", response_model=Offspring)
def show_isuper_offspring(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Offspring not found")
    return record

@router.post("/", response_model=Offspring, status_code=201)
def create_isuper_offspring(payload: OffspringInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=Offspring)
def update_isuper_offspring(item_id: int, payload: OffspringInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Offspring not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_offspring(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Offspring not found")
    return {"success": True}
