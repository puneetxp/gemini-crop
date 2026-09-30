"""
LivestockMarketplaceListing ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class LivestockMarketplaceListing(Model):
    """LivestockMarketplaceListing model for livestock_marketplace_listings table"""
    
    table = 'livestock_marketplace_listings'
    
    fillable = [
        'enable',
        'listing_type',
        'asking_price',
        'current_age_months',
        'current_weight_kg',
        'milk_production_liters_per_day',
        'breeding_history',
        'health_status',
        'vaccination_status',
        'total_investment',
        'total_revenue',
        'current_roi_percentage',
        'break_even_achieved',
        'break_even_date',
        'projected_annual_profit',
        'location_state',
        'location_district',
        'farmer_contact_phone',
        'farmer_contact_email',
        'listing_status',
        'views_count',
        'bedrock_analysis',
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
