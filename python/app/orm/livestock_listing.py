"""
LivestockListing ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class LivestockListing(Model):
    """LivestockListing model for livestock_listings table"""
    
    table = 'livestock_listings'
    
    fillable = [
        'enable',
        'title',
        'description',
        'species',
        'breed',
        'age_years',
        'age_months',
        'gender',
        'quantity',
        'purpose',
        'price',
        'price_negotiable',
        'weight_kg',
        'health_status',
        'vaccination_status',
        'last_vaccination_date',
        'milk_production_liters',
        'breeding_certified',
        'breeding_certification_number',
        'genetic_lineage',
        'photos',
        'videos',
        'location_state',
        'location_district',
        'location_village',
        'latitude',
        'longitude',
        'pincode',
        'address_line',
        'farmer_contact_phone',
        'farmer_contact_email',
        'status',
        'views_count',
        'interest_count',
        'inquiry_count',
        'featured',
        'featured_until',
        'livestock_id',
        'farmer_id',
    ]
    
    relations = {
            'livestock': {
                'name': 'livestock_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.livestock', fromlist=['Livestock']).Livestock
            },
            'farmer': {
                'name': 'farmer_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
