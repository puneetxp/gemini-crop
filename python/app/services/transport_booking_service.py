from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.transport_booking import TransportBooking


class TransportBookingService(CrudService):
    model = TransportBooking


# Singleton instance
_service = TransportBookingService()


# Generic getter (for auto-generated routers)
def get_service() -> TransportBookingService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_transport_booking_service() -> TransportBookingService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
