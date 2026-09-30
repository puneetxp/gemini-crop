"""
Crop ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class Crop(Model):
    """Crop model for crops table"""
    
    table = 'crops'
    
    fillable = [
        'enable',
        'crop_name',
        'crop_variety',
        'season',
        'planting_date',
        'expected_harvest_date',
        'area',
        'expected_yield',
        'expected_profit',
        'actual_yield',
        'actual_profit',
        'status',
        'parent_crop_id',
        'crop_role',
        'farm_plot_id',
        'strategy_id',
    ]
    
    relations = {
            'farm_plot': {
                'name': 'farm_plot_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm_plot', fromlist=['FarmPlot']).FarmPlot
            },
            'strategy': {
                'name': 'strategy_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.annual_strategy', fromlist=['AnnualStrategy']).AnnualStrategy
            },
            'crop_expense': {
                'name': 'id',
                'key': 'crop_id',
                'callback': lambda: __import__('app.orm.crop_expense', fromlist=['CropExpense']).CropExpense
            },
            'crop_milestone': {
                'name': 'id',
                'key': 'crop_id',
                'callback': lambda: __import__('app.orm.crop_milestone', fromlist=['CropMilestone']).CropMilestone
            },
            'fertilizer_application': {
                'name': 'id',
                'key': 'crop_id',
                'callback': lambda: __import__('app.orm.fertilizer_application', fromlist=['FertilizerApplication']).FertilizerApplication
            },
            'pest_disease_alert': {
                'name': 'id',
                'key': 'crop_id',
                'callback': lambda: __import__('app.orm.pest_disease_alert', fromlist=['PestDiseaseAlert']).PestDiseaseAlert
            },
    }
