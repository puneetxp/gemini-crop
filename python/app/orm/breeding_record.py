"""
BreedingRecord ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class BreedingRecord(Model):
    """BreedingRecord model for breeding_records table"""
    
    table = 'breeding_records'
    
    fillable = [
        'enable',
        'breeding_type',
        'breeding_date',
        'mate_breed',
        'expected_delivery_date',
        'actual_delivery_date',
        'pregnancy_status',
        'number_of_offspring',
        'breeding_cost',
        'veterinarian_name',
        'notes',
        'livestock_id',
        'farmer_id',
        'mate_id',
    ]
    
    relations = {
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
            'mate': {
                'name': 'mate_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.livestock', fromlist=['Livestock']).Livestock
            },
            'offspring': {
                'name': 'id',
                'key': 'breeding_record_id',
                'callback': lambda: __import__('app.orm.offspring', fromlist=['Offspring']).Offspring
            },
    }
