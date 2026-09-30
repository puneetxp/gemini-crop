from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.voice_assist_log import VoiceAssistLog


class VoiceAssistLogService(CrudService):
    model = VoiceAssistLog


# Singleton instance
_service = VoiceAssistLogService()


# Generic getter (for auto-generated routers)
def get_service() -> VoiceAssistLogService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_voice_assist_log_service() -> VoiceAssistLogService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
