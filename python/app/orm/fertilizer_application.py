"""
FertilizerApplication ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class FertilizerApplication(Model):
    """FertilizerApplication model for fertilizer_applications table"""
    
    table = 'fertilizer_applications'
    
    fillable = [
        'enable',
        'application_date',
        'fertilizer_type',
        'category',
        'quantity_kg',
        'quantity_per_hectare',
        'area_applied_hectares',
        'nitrogen_kg',
        'phosphorus_kg',
        'potassium_kg',
        'cost_total',
        'cost_per_kg',
        'cost_per_hectare',
        'application_method',
        'growth_stage',
        'days_after_planting',
        'effectiveness_score',
        'soil_response_notes',
        'weather_conditions',
        'temperature_celsius',
        'rainfall_mm_24h',
        'recommended_by',
        'recommendation_id',
        'notes',
        'farm_id',
        'plot_id',
        'crop_id',
        'soil_test_before_id',
        'soil_test_after_id',
    ]
    
    relations = {
            'farm': {
                'name': 'farm_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm', fromlist=['Farm']).Farm
            },
            'plot': {
                'name': 'plot_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm_plot', fromlist=['FarmPlot']).FarmPlot
            },
            'crop': {
                'name': 'crop_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.crop', fromlist=['Crop']).Crop
            },
            'soil_test_before': {
                'name': 'soil_test_before_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.soil_test_result', fromlist=['SoilTestResult']).SoilTestResult
            },
            'soil_test_after': {
                'name': 'soil_test_after_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.soil_test_result', fromlist=['SoilTestResult']).SoilTestResult
            },
    }
