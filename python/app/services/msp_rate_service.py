from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.msp_rate import MspRate


class MspRateService(CrudService):
    model = MspRate


# Singleton instance
_service = MspRateService()


# Generic getter (for auto-generated routers)
def get_service() -> MspRateService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_msp_rate_service() -> MspRateService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
