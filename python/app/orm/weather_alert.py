"""
WeatherAlert ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class WeatherAlert(Model):
    """WeatherAlert model for weather_alerts table"""
    
    table = 'weather_alerts'
    
    fillable = [
        'enable',
        'state',
        'district',
        'alert_type',
        'severity',
        'message',
        'recommendation',
        'valid_from',
        'valid_until',
        'is_active',
        'farm_id',
    ]
    
    relations = {
            'farm': {
                'name': 'farm_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm', fromlist=['Farm']).Farm
            },
    }
