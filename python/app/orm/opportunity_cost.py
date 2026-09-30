"""
OpportunityCost ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class OpportunityCost(Model):
    """OpportunityCost model for opportunity_costs table"""
    
    table = 'opportunity_costs'
    
    fillable = [
        'enable',
        'location_state',
        'location_district',
        'primary_crop',
        'alternative_crop',
        'season',
        'year',
        'primary_crop_profit',
        'alternative_crop_profit',
        'profit_difference',
        'primary_crop_investment',
        'alternative_crop_investment',
        'investment_difference',
        'primary_crop_roi',
        'alternative_crop_roi',
        'roi_difference',
        'primary_crop_risk',
        'alternative_crop_risk',
        'risk_factor',
        'primary_crop_demand',
        'alternative_crop_demand',
        'market_stability_comparison',
        'recommended_choice',
        'recommendation_confidence',
        'recommendation_reasoning',
        'soil_suitability_comparison',
        'water_requirement_comparison',
        'labor_requirement_comparison',
    ]
