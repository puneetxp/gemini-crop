"""
PestDiseaseData ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class PestDiseaseData(Model):
    """PestDiseaseData model for pest_disease_data table"""
    
    table = 'pest_disease_data'
    
    fillable = [
        'enable',
        'name',
        'type',
        'scientific_name',
        'description',
        'affected_crops',
        'risk_stages',
        'temperature_min',
        'temperature_max',
        'humidity_min',
        'humidity_max',
        'rainfall_min',
        'severity',
        'organic_treatments',
        'chemical_treatments',
        'prevention_measures',
        'timing_instructions',
        'data_source',
        'last_updated',
    ]
