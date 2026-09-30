"""
LivestockRoiPrediction ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class LivestockRoiPrediction(Model):
    """LivestockRoiPrediction model for livestock_roi_predictions table"""
    
    table = 'livestock_roi_predictions'
    
    fillable = [
        'enable',
        'prediction_date',
        'prediction_type',
        'species',
        'breed',
        'age_months',
        'purpose',
        'purchase_price',
        'initial_setup_cost',
        'total_initial_investment',
        'monthly_feed_cost',
        'monthly_healthcare_cost',
        'monthly_labor_cost',
        'monthly_other_costs',
        'total_monthly_cost',
        'monthly_milk_revenue',
        'monthly_egg_revenue',
        'monthly_wool_revenue',
        'monthly_manure_revenue',
        'total_monthly_revenue',
        'offspring_revenue_per_year',
        'expected_sale_value',
        'expected_productive_years',
        'break_even_months',
        'break_even_date',
        'roi_1_year',
        'roi_2_year',
        'roi_5_year',
        'roi_percentage_1_year',
        'roi_percentage_2_year',
        'roi_percentage_5_year',
        'monthly_net_profit',
        'annual_net_profit',
        'lifetime_net_profit',
        'comparison_with_alternatives',
        'market_price_trends',
        'risk_level',
        'risk_factors',
        'mortality_risk',
        'disease_risk',
        'market_risk',
        'confidence_score',
        'key_assumptions',
        'sensitivity_analysis',
        'recommendation',
        'optimization_suggestions',
        'market_data_source',
        'breed_performance_data_source',
        'animal_id',
        'user_id',
    ]
    
    relations = {
            'animal': {
                'name': 'animal_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.livestock', fromlist=['Livestock']).Livestock
            },
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
