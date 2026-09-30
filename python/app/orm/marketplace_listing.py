"""
MarketplaceListing ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class MarketplaceListing(Model):
    """MarketplaceListing model for marketplace_listings table"""
    
    table = 'marketplace_listings'
    
    fillable = [
        'enable',
        'crop_type',
        'crop_variety',
        'expected_harvest_date',
        'estimated_quantity',
        'available_quantity',
        'quality_grade',
        'location_state',
        'location_district',
        'farmer_contact_phone',
        'farmer_contact_email',
        'status',
        'delivery_latitude',
        'delivery_longitude',
        'delivery_pincode',
        'delivery_village',
        'delivery_address_line',
        'embedding',
        'embedding_cache_key',
        'price_per_unit',
        'farm_id',
        'farmer_id',
    ]
    
    relations = {
            'farm': {
                'name': 'farm_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm', fromlist=['Farm']).Farm
            },
            'farmer': {
                'name': 'farmer_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
