from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.satellite_observation import SatelliteObservation


class SatelliteObservationService(CrudService):
    model = SatelliteObservation


# Singleton instance
_service = SatelliteObservationService()


# Generic getter (for auto-generated routers)
def get_service() -> SatelliteObservationService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_satellite_observation_service() -> SatelliteObservationService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
