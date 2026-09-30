"""
LivestockTransaction ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class LivestockTransaction(Model):
    """LivestockTransaction model for livestock_transactions table"""
    
    table = 'livestock_transactions'
    
    fillable = [
        'enable',
        'transaction_type',
        'quantity',
        'agreed_price',
        'status',
        'buyer_message',
        'seller_response',
        'buyer_contact_phone',
        'buyer_contact_email',
        'delivery_required',
        'delivery_address',
        'delivery_latitude',
        'delivery_longitude',
        'health_guarantee_days',
        'health_guarantee_expires',
        'completed_at',
        'cancelled_at',
        'cancellation_reason',
        'notes',
        'listing_id',
        'seller_id',
        'buyer_id',
    ]
    
    relations = {
            'listing': {
                'name': 'listing_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.livestock_listing', fromlist=['LivestockListing']).LivestockListing
            },
            'seller': {
                'name': 'seller_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
            'buyer': {
                'name': 'buyer_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
