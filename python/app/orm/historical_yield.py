"""
HistoricalYield ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class HistoricalYield(Model):
    """HistoricalYield model for historical_yields table"""
    
    table = 'historical_yields'
    
    fillable = [
        'enable',
        'crop_type',
        'variety',
        'state',
        'district',
        'block',
        'year',
        'season',
        'avg_yield_per_acre',
        'min_yield',
        'max_yield',
        'success_rate',
        'farmer_count',
        'total_area_cultivated',
        'soil_types',
        'irrigation_methods',
        'avg_rainfall',
        'avg_temperature',
        'quality_distribution',
        'avg_quality_grade',
        'data_source',
        'data_quality_score',
    ]
