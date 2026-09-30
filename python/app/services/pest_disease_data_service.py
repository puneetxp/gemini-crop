from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.pest_disease_data import PestDiseaseData


class PestDiseaseDataService(CrudService):
    model = PestDiseaseData


# Singleton instance
_service = PestDiseaseDataService()


# Generic getter (for auto-generated routers)
def get_service() -> PestDiseaseDataService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_pest_disease_data_service() -> PestDiseaseDataService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
