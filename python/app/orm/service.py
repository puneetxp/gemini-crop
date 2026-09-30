"""
Service ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class Service(Model):
    """Service model for services table"""
    
    table = 'services'
    
    fillable = [
        'enable',
        'category',
        'name',
        'organisation',
        'description',
        'phone',
        'whatsapp',
        'email',
        'location_state',
        'location_district',
        'address',
        'languages',
        'available_now',
        'verified',
        'is_active',
        'added_by_user_id',
        'user_id',
    ]
