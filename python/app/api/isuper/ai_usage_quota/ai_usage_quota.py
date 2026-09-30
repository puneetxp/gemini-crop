from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.ai_usage_quota import AiUsageQuota, AiUsageQuotaInput
from app.services.ai_usage_quota_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/ai_usage_quota", tags=["isuper-ai_usage_quota"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[AiUsageQuota])
def list_isuper_ai_usage_quota():
    return service.all()

@router.get("/{item_id}", response_model=AiUsageQuota)
def show_isuper_ai_usage_quota(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Ai_usage_quota not found")
    return record

@router.post("/", response_model=AiUsageQuota, status_code=201)
def create_isuper_ai_usage_quota(payload: AiUsageQuotaInput):
    return service.create(payload.dict(exclude_unset=True))

@router.put("/{item_id}", response_model=AiUsageQuota)
def update_isuper_ai_usage_quota(item_id: int, payload: AiUsageQuotaInput):
    updated = service.update(item_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Ai_usage_quota not found")
    return updated

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_ai_usage_quota(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Ai_usage_quota not found")
    return {"success": True}
