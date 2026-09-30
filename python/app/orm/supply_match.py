"""
SupplyMatch ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SupplyMatch(Model):
    """SupplyMatch model for supply_matches table"""
    
    table = 'supply_matches'
    
    fillable = [
        'enable',
        'matched_quantity',
        'match_score',
        'price_offered',
        'status',
        'match_explanation',
        'is_aggregated',
        'aggregation_group_id',
        'farmer_confirmation_status',
        'farmer_confirmed_at',
        'buyer_accepted_at',
        'delivery_status',
        'delivery_notes',
        'request_id',
        'listing_id',
        'farmer_id',
    ]
    
    relations = {
            'request': {
                'name': 'request_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.supply_request', fromlist=['SupplyRequest']).SupplyRequest
            },
            'listing': {
                'name': 'listing_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.marketplace_listing', fromlist=['MarketplaceListing']).MarketplaceListing
            },
            'farmer': {
                'name': 'farmer_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
