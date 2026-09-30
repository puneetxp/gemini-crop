"""
SoilTest ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SoilTest(Model):
    """SoilTest model for soil_tests table"""
    
    table = 'soil_tests'
    
    fillable = [
        'enable',
        'test_date',
        'test_type',
        'testing_lab',
        'lab_report_url',
        'soil_type',
        'soil_texture',
        'soil_color',
        'ph_level',
        'electrical_conductivity',
        'organic_carbon',
        'organic_matter',
        'nitrogen_n',
        'phosphorus_p',
        'potassium_k',
        'calcium_ca',
        'magnesium_mg',
        'sulfur_s',
        'iron_fe',
        'manganese_mn',
        'zinc_zn',
        'copper_cu',
        'boron_b',
        'molybdenum_mo',
        'nitrogen_status',
        'phosphorus_status',
        'potassium_status',
        'water_holding_capacity',
        'drainage_quality',
        'bulk_density',
        'porosity',
        'microbial_activity',
        'earthworm_count',
        'overall_health_score',
        'fertility_rating',
        'lab_recommendations',
        'fertilizer_recommendations',
        'amendment_recommendations',
        'test_cost',
        'plot_id',
    ]
    
    relations = {
            'plot': {
                'name': 'plot_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm_plot', fromlist=['FarmPlot']).FarmPlot
            },
    }
