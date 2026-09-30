"""
Voice/assistant audit log: one row in voice_assist_logs per /voice/assist call,
so "voice isn't picking up" can be diagnosed from data (what the model heard,
which model answered, and the exact error) instead of guessing.

Kept out of voice_assist_log_service.py because the generator overwrites that file.
Logging never breaks the request: failures are only written to the app log.
"""

import logging
from typing import Any, Optional

from app.core.db import DB

logger = logging.getLogger(__name__)


def _cut(value: Optional[str], limit: int) -> Optional[str]:
    return value[:limit] if isinstance(value, str) else value


def record_attempt(
    user_id: Any,
    *,
    source: str,
    task: Optional[str] = None,
    ui_lang: Optional[str] = None,
    language_detected: Optional[str] = None,
    mime_type: Optional[str] = None,
    audio_bytes: Optional[int] = None,
    duration_ms: Optional[int] = None,
    transcript: Optional[str] = None,
    intent: Optional[str] = None,
    model_used: Optional[str] = None,
    status: str = "ok",
    error: Optional[str] = None,
    latency_ms: Optional[int] = None,
) -> None:
    try:
        DB.raw(
            """INSERT INTO voice_assist_logs
               (user_id, source, task, ui_lang, language_detected, mime_type, audio_bytes, duration_ms,
                transcript, intent, model_used, status, error, latency_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                int(user_id),
                source,
                task,
                _cut(ui_lang, 10),
                _cut(language_detected, 10),
                _cut(mime_type, 50),
                audio_bytes,
                duration_ms,
                _cut(transcript, 4000),
                _cut(intent, 20),
                _cut(model_used, 100),
                status,
                _cut(error, 4000),
                latency_ms,
            ],
        )
    except Exception as e:
        logger.warning(f"voice_assist_logs insert failed: {e}")
