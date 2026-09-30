from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.quality_verification import QualityVerification


class QualityVerificationService(CrudService):
    model = QualityVerification


# Singleton instance
_service = QualityVerificationService()


# Generic getter (for auto-generated routers)
def get_service() -> QualityVerificationService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_quality_verification_service() -> QualityVerificationService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
