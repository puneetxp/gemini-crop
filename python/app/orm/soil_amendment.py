"""
SoilAmendment ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SoilAmendment(Model):
    """SoilAmendment model for soil_amendments table"""
    
    table = 'soil_amendments'
    
    fillable = [
        'enable',
        'amendment_date',
        'amendment_type',
        'amendment_name',
        'primary_purpose',
        'target_improvement',
        'quantity',
        'unit',
        'quantity_per_acre',
        'application_method',
        'incorporation_depth',
        'cost',
        'cost_per_acre',
        'organic_matter_content',
        'nutrient_content',
        'carbon_nitrogen_ratio',
        'current_ph',
        'target_ph',
        'expected_ph_change',
        'days_before_planting',
        'soil_moisture_at_application',
        'weather_conditions',
        'expected_benefits',
        'expected_duration_months',
        'actual_benefits',
        'effectiveness_rating',
        'recommendation_source',
        'recommended_by',
        'notes',
        'plot_id',
        'follow_up_soil_test_id',
    ]
    
    relations = {
            'plot': {
                'name': 'plot_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm_plot', fromlist=['FarmPlot']).FarmPlot
            },
            'follow_up_soil_test': {
                'name': 'follow_up_soil_test_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.soil_test', fromlist=['SoilTest']).SoilTest
            },
    }
