"""
Veterinarian ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class Veterinarian(Model):
    """Veterinarian model for veterinarians table"""
    
    table = 'veterinarians'
    
    fillable = [
        'enable',
        'added_by_user_id',
        'name',
        'clinic_name',
        'specialization',
        'species_supported',
        'phone',
        'whatsapp',
        'email',
        'location_state',
        'location_district',
        'address',
        'available_now',
        'verified',
        'rating',
        'total_ratings',
        'notes',
    ]
