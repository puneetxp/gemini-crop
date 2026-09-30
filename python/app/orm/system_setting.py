"""
SystemSetting ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SystemSetting(Model):
    """SystemSetting model for system_settings table"""
    
    table = 'system_settings'
    
    fillable = [
        'enable',
        'key',
        'value',
        'description',
    ]
