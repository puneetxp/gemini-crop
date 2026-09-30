from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.slusi_microwatershed_map import SlusiMicrowatershedMap


class SlusiMicrowatershedMapService(CrudService):
    model = SlusiMicrowatershedMap


# Singleton instance
_service = SlusiMicrowatershedMapService()


# Generic getter (for auto-generated routers)
def get_service() -> SlusiMicrowatershedMapService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_slusi_microwatershed_map_service() -> SlusiMicrowatershedMapService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
