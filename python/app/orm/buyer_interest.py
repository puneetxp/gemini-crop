"""
BuyerInterest ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class BuyerInterest(Model):
    """BuyerInterest model for buyer_interests table"""
    
    table = 'buyer_interests'
    
    fillable = [
        'enable',
        'buyer_name',
        'buyer_phone',
        'buyer_email',
        'buyer_type',
        'interested_quantity',
        'message',
        'status',
        'delivery_latitude',
        'delivery_longitude',
        'delivery_pincode',
        'delivery_state',
        'delivery_district',
        'delivery_village',
        'delivery_address_line',
        'listing_id',
    ]
    
    relations = {
            'listing': {
                'name': 'listing_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.marketplace_listing', fromlist=['MarketplaceListing']).MarketplaceListing
            },
    }
