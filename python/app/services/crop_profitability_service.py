from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.crop_profitability import CropProfitability


class CropProfitabilityService(CrudService):
    model = CropProfitability


# Singleton instance
_service = CropProfitabilityService()


# Generic getter (for auto-generated routers)
def get_service() -> CropProfitabilityService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_crop_profitability_service() -> CropProfitabilityService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
