"""
CropMarketData ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class CropMarketData(Model):
    """CropMarketData model for crop_market_data table"""
    
    table = 'crop_market_data'
    
    fillable = [
        'enable',
        'crop_name',
        'state',
        'district',
        'price_per_kg',
        'date',
        'season',
        'yoy_growth',
        'demand_level',
    ]
