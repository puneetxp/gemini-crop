"""
MspRate ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class MspRate(Model):
    """MspRate model for msp_rates table"""
    
    table = 'msp_rates'
    
    fillable = [
        'enable',
        'crop_name',
        'year',
        'season',
        'msp_per_quintal',
        'msp_per_kg',
        'increase_over_previous',
        'cost_of_production',
        'return_over_cost_percent',
        'source',
    ]
