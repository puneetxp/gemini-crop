from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.crop_diagnosis import CropDiagnosis


class CropDiagnosisService(CrudService):
    model = CropDiagnosis


# Singleton instance
_service = CropDiagnosisService()


# Generic getter (for auto-generated routers)
def get_service() -> CropDiagnosisService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_crop_diagnosis_service() -> CropDiagnosisService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
