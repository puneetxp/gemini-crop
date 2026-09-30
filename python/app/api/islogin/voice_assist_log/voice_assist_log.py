from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.voice_assist_log import VoiceAssistLog, VoiceAssistLogInput
from app.services.voice_assist_log_service import get_service
from app.core.auth import get_current_active_user
from typing import List


router = APIRouter(prefix="/islogin/voice_assist_log", tags=["islogin-voice_assist_log"])
service = get_service()

@router.get("/", response_model=List[VoiceAssistLog])
def list_islogin_voice_assist_log(current_user=Depends(get_current_active_user)):
    return service.all(owner=current_user)

@router.get("/{item_id}", response_model=VoiceAssistLog)
def show_islogin_voice_assist_log(item_id: int, current_user=Depends(get_current_active_user)):
    record = service.find(item_id, owner=current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Voice_assist_log not found")
    return record
