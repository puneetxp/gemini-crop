from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.advance_booking import AdvanceBooking


class AdvanceBookingService(CrudService):
    model = AdvanceBooking


# Singleton instance
_service = AdvanceBookingService()


# Generic getter (for auto-generated routers)
def get_service() -> AdvanceBookingService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_advance_booking_service() -> AdvanceBookingService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
