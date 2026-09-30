from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from app.models.voice_assist_log import VoiceAssistLog, VoiceAssistLogInput
from app.services.voice_assist_log_service import get_service
from app.core.auth import get_current_admin
from typing import List, Dict


router = APIRouter(prefix="/isuper/voice_assist_log", tags=["isuper-voice_assist_log"],
                   dependencies=[Depends(get_current_admin)])
service = get_service()

@router.get("/", response_model=List[VoiceAssistLog])
def list_isuper_voice_assist_log():
    return service.all()

@router.get("/{item_id}", response_model=VoiceAssistLog)
def show_isuper_voice_assist_log(item_id: int):
    record = service.find(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="Voice_assist_log not found")
    return record

@router.delete("/{item_id}", response_model=Dict[str, bool])
def delete_isuper_voice_assist_log(item_id: int):
    if not service.delete(item_id):
        raise HTTPException(status_code=404, detail="Voice_assist_log not found")
    return {"success": True}
