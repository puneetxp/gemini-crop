"""
TransportProvider ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class TransportProvider(Model):
    """TransportProvider model for transport_providers table"""
    
    table = 'transport_providers'
    
    fillable = [
        'enable',
        'company_name',
        'contact_person',
        'contact_phone',
        'contact_email',
        'service_areas',
        'vehicle_types',
        'livestock_specialization',
        'base_rate_per_km',
        'minimum_charge',
        'insurance_available',
        'insurance_rate_percentage',
        'max_capacity_animals',
        'rating',
        'total_ratings',
        'completed_transports',
        'verified',
        'verification_documents',
        'license_number',
        'status',
        'user_id',
    ]
    
    relations = {
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
