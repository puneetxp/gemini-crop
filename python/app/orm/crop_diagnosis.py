"""
CropDiagnosis ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class CropDiagnosis(Model):
    """CropDiagnosis model for crop_diagnoses table"""
    
    table = 'crop_diagnoses'
    
    fillable = [
        'enable',
        'crop_id',
        'farm_id',
        'crop_name',
        'state',
        'district',
        'disease_name',
        'scientific_name',
        'category',
        'severity',
        'urgency',
        'confidence',
        'language',
        'model_used',
        'safety_flags',
        'result',
        'user_id',
    ]
    
    relations = {
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
