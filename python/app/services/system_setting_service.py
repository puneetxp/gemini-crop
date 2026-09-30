from __future__ import annotations

from app.core.crud_service import CrudService
from app.orm.system_setting import SystemSetting


class SystemSettingService(CrudService):
    model = SystemSetting


# Singleton instance
_service = SystemSettingService()


# Generic getter (for auto-generated routers)
def get_service() -> SystemSettingService:
    """Get service instance (generic name for auto-generated code)"""
    return _service


# Specific getter (for manual/custom code compatibility)
def get_system_setting_service() -> SystemSettingService:
    """Get service instance (specific name for backward compatibility)"""
    return _service
