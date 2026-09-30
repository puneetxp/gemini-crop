"""
PricePrediction ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class PricePrediction(Model):
    """PricePrediction model for price_predictions table"""
    
    table = 'price_predictions'
    
    fillable = [
        'enable',
        'item_type',
        'item_name',
        'variety',
        'state',
        'district',
        'prediction_date',
        'target_date',
        'predicted_price',
        'confidence_score',
        'price_range_min',
        'price_range_max',
        'trend',
        'demand_forecast',
        'supply_forecast',
        'season',
        'model_version',
        'factors',
    ]
