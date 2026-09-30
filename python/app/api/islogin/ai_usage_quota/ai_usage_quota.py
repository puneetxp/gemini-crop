from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.ai_usage_quota import AiUsageQuota, AiUsageQuotaInput
from app.services.ai_usage_quota_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/ai_usage_quota", tags=["islogin-ai_usage_quota"])
service = get_service()

@router.get("/", response_model=List[AiUsageQuota])
def list_islogin_ai_usage_quota(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=AiUsageQuota)
def show_islogin_ai_usage_quota(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Ai_usage_quota not found")
    return record
