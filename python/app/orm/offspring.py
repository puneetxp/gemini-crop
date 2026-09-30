"""
Offspring ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class Offspring(Model):
    """Offspring model for offspring table"""
    
    table = 'offspring'
    
    fillable = [
        'enable',
        'birth_date',
        'gender',
        'birth_weight',
        'health_status',
        'current_weight',
        'growth_rate',
        'weaning_date',
        'sale_date',
        'sale_price',
        'notes',
        'breeding_record_id',
        'livestock_id',
        'farmer_id',
    ]
    
    relations = {
            'breeding_record': {
                'name': 'breeding_record_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.breeding_record', fromlist=['BreedingRecord']).BreedingRecord
            },
            'livestock': {
                'name': 'livestock_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.livestock', fromlist=['Livestock']).Livestock
            },
            'farmer': {
                'name': 'farmer_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
