from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.soil_moisture_data import SoilMoistureData


class SoilMoistureDataService(CrudService):
    model = SoilMoistureData


# Singleton instance
_service = SoilMoistureDataService()


# Generic getter (for auto-generated routers)
def get_service() -> SoilMoistureDataService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_soil_moisture_data_service() -> SoilMoistureDataService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
