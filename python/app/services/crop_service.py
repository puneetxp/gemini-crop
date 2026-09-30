from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.crop import Crop


class CropService(CrudService):
    model = Crop


# Singleton instance
_service = CropService()


# Generic getter (for auto-generated routers)
def get_service() -> CropService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_crop_service() -> CropService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
