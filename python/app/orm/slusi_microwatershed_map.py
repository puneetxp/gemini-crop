"""
SlusiMicrowatershedMap ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SlusiMicrowatershedMap(Model):
    """SlusiMicrowatershedMap model for slusi_microwatershed_maps table"""
    
    table = 'slusi_microwatershed_maps'
    
    fillable = [
        'enable',
        'state',
        'map_data',
        'file_size_bytes',
        'ingested_at',
    ]
