from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.farm_plot import FarmPlot


class FarmPlotService(CrudService):
    model = FarmPlot


# Singleton instance
_service = FarmPlotService()


# Generic getter (for auto-generated routers)
def get_service() -> FarmPlotService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_farm_plot_service() -> FarmPlotService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
