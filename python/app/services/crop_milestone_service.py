from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.crop_milestone import CropMilestone


class CropMilestoneService(CrudService):
    model = CropMilestone


# Singleton instance
_service = CropMilestoneService()


# Generic getter (for auto-generated routers)
def get_service() -> CropMilestoneService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_crop_milestone_service() -> CropMilestoneService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
