from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.slusi_lcc_report import SlusiLccReport


class SlusiLccReportService(CrudService):
    model = SlusiLccReport


# Singleton instance
_service = SlusiLccReportService()


# Generic getter (for auto-generated routers)
def get_service() -> SlusiLccReportService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_slusi_lcc_report_service() -> SlusiLccReportService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
