"""
CropExpense ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class CropExpense(Model):
    """CropExpense model for crop_expenses table"""
    
    table = 'crop_expenses'
    
    fillable = [
        'enable',
        'category',
        'amount',
        'description',
        'expense_date',
        'crop_id',
    ]
    
    relations = {
            'crop': {
                'name': 'crop_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.crop', fromlist=['Crop']).Crop
            },
    }
