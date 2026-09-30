"""
SupplyRequest ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SupplyRequest(Model):
    """SupplyRequest model for supply_requests table"""
    
    table = 'supply_requests'
    
    fillable = [
        'enable',
        'crop_type',
        'quantity_needed',
        'quality_requirements',
        'delivery_date_start',
        'delivery_date_end',
        'max_price_per_unit',
        'recurring',
        'recurrence_pattern',
        'is_emergency',
        'status',
        'delivery_address',
        'delivery_latitude',
        'delivery_longitude',
        'delivery_pincode',
        'delivery_state',
        'delivery_district',
        'notes',
        'embedding',
        'embedding_cache_key',
        'buyer_id',
    ]
    
    relations = {
            'buyer': {
                'name': 'buyer_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
