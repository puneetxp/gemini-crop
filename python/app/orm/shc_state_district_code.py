"""
ShcStateDistrictCode ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class ShcStateDistrictCode(Model):
    """ShcStateDistrictCode model for shc_state_district_codes table"""
    
    table = 'shc_state_district_codes'
    
    fillable = [
        'enable',
        'state_name',
        'state_code',
        'district_name',
        'district_code',
    ]
