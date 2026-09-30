"""
SoilMoistureData ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SoilMoistureData(Model):
    """SoilMoistureData model for soil_moisture_data table"""
    
    table = 'soil_moisture_data'
    
    fillable = [
        'enable',
        'state',
        'district',
        'date',
        'year',
        'month',
        'moisture_level',
        'agency_name',
    ]
