from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.ai_usage_quota import AiUsageQuota


class AiUsageQuotaService(CrudService):
    model = AiUsageQuota


# Singleton instance
_service = AiUsageQuotaService()


# Generic getter (for auto-generated routers)
def get_service() -> AiUsageQuotaService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_ai_usage_quota_service() -> AiUsageQuotaService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
