"""
SeasonalTrend ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SeasonalTrend(Model):
    """SeasonalTrend model for seasonal_trends table"""
    
    table = 'seasonal_trends'
    
    fillable = [
        'enable',
        'crop_type',
        'state',
        'district',
        'planting_season',
        'harvest_season',
        'optimal_planting_start',
        'optimal_planting_end',
        'optimal_harvest_start',
        'optimal_harvest_end',
        'avg_growth_duration_days',
        'price_trend_yoy',
        'demand_trend_yoy',
        'yield_trend_yoy',
        'weather_suitability_score',
        'pest_disease_risk',
        'market_timing_score',
        'avg_success_rate',
        'farmer_adoption_rate',
        'recommended_varieties',
        'companion_crops',
        'rotation_recommendations',
        'analysis_start_year',
        'analysis_end_year',
        'years_of_data',
    ]
