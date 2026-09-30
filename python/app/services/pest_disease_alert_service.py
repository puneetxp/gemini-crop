from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.pest_disease_alert import PestDiseaseAlert


class PestDiseaseAlertService(CrudService):
    model = PestDiseaseAlert


# Singleton instance
_service = PestDiseaseAlertService()


# Generic getter (for auto-generated routers)
def get_service() -> PestDiseaseAlertService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_pest_disease_alert_service() -> PestDiseaseAlertService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
