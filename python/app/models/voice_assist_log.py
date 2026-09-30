from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from datetime import datetime as _datetime


class VoiceAssistLog(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    source: str
    task: str | None = None
    ui_lang: str | None = None
    language_detected: str | None = None
    mime_type: str | None = None
    audio_bytes: int | None = None
    duration_ms: int | None = None
    transcript: str | None = None
    intent: str | None = None
    model_used: str | None = None
    status: str
    error: str | None = None
    latency_ms: int | None = None
    user_id: int


class VoiceAssistLogInput(BaseModel):
    enable: int | None = None
    source: str | None = None
    task: str | None = None
    ui_lang: str | None = None
    language_detected: str | None = None
    mime_type: str | None = None
    audio_bytes: int | None = None
    duration_ms: int | None = None
    transcript: str | None = None
    intent: str | None = None
    model_used: str | None = None
    status: str | None = None
    error: str | None = None
    latency_ms: int | None = None
    user_id: int | None = None
