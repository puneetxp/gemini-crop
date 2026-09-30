"""
Livestock ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class Livestock(Model):
    """Livestock model for livestock table"""
    
    table = 'livestock'
    
    fillable = [
        'enable',
        'species',
        'breed',
        'name',
        'quantity',
        'purchase_price',
        'purchase_date',
        'purpose',
        'expected_roi',
        'break_even_date',
        'status',
        'latitude',
        'longitude',
        'pincode',
        'state',
        'district',
        'village',
        'address_line',
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
            'breeding_record': {
                'name': 'id',
                'key': 'livestock_id',
                'callback': lambda: __import__('app.orm.breeding_record', fromlist=['BreedingRecord']).BreedingRecord
            },
            'livestock_health_record': {
                'name': 'id',
                'key': 'livestock_id',
                'callback': lambda: __import__('app.orm.livestock_health_record', fromlist=['LivestockHealthRecord']).LivestockHealthRecord
            },
            'livestock_listing': {
                'name': 'id',
                'key': 'livestock_id',
                'callback': lambda: __import__('app.orm.livestock_listing', fromlist=['LivestockListing']).LivestockListing
            },
            'livestock_marketplace_listing': {
                'name': 'id',
                'key': 'livestock_id',
                'callback': lambda: __import__('app.orm.livestock_marketplace_listing', fromlist=['LivestockMarketplaceListing']).LivestockMarketplaceListing
            },
            'offspring': {
                'name': 'id',
                'key': 'livestock_id',
                'callback': lambda: __import__('app.orm.offspring', fromlist=['Offspring']).Offspring
            },
    }
