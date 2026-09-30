"""
CropProfitability ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class CropProfitability(Model):
    """CropProfitability model for crop_profitability table"""
    
    table = 'crop_profitability'
    
    fillable = [
        'enable',
        'crop_type',
        'variety',
        'state',
        'district',
        'year',
        'season',
        'avg_profit_per_acre',
        'min_profit_per_acre',
        'max_profit_per_acre',
        'seed_cost',
        'fertilizer_cost',
        'pesticide_cost',
        'labor_cost',
        'irrigation_cost',
        'equipment_cost',
        'other_costs',
        'total_investment_cost',
        'avg_revenue_per_acre',
        'roi_percentage',
        'break_even_yield',
        'profit_margin',
        'risk_level',
        'price_risk_score',
        'yield_risk_score',
        'market_demand',
        'competition_level',
        'data_source',
        'sample_size',
    ]
