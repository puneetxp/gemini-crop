"""
SatelliteObservation ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SatelliteObservation(Model):
    """SatelliteObservation model for satellite_observations table"""
    
    table = 'satellite_observations'
    
    fillable = [
        'enable',
        'scene_id',
        'observed_on',
        'source',
        'ndvi',
        'ndmi',
        'ndre',
        'clear_pct',
        'pixels',
        'state',
        'district',
        'farm_id',
    ]
    
    relations = {
            'farm': {
                'name': 'farm_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.farm', fromlist=['Farm']).Farm
            },
    }
