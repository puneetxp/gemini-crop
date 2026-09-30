"""
FarmPlot ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class FarmPlot(Model):
    """FarmPlot model for farm_plots table"""
    
    table = 'farm_plots'
    
    fillable = [
        'enable',
        'plot_name',
        'area',
        'soil_type',
        'irrigation_type',
        'state',
        'district',
        'previous_crops',
        'investment_capacity',
        'nitrogen',
        'phosphorus',
        'potassium',
        'ph_level',
        'organic_carbon',
        'electrical_conductivity',
        'sulfur',
        'zinc',
        'iron',
        'boron',
        'farm_id',
    ]
    
    relations = {
            'farm': {
                'name': 'farm_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm', fromlist=['Farm']).Farm
            },
            'crop': {
                'name': 'id',
                'key': 'farm_plot_id',
                'callback': lambda: __import__('app.orm.crop', fromlist=['Crop']).Crop
            },
    }
