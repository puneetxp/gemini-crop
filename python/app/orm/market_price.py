"""
MarketPrice ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class MarketPrice(Model):
    """MarketPrice model for market_prices table"""
    
    table = 'market_prices'
    
    fillable = [
        'enable',
        'item_type',
        'item_name',
        'variety',
        'price_per_unit',
        'quantity',
        'total_value',
        'quality_grade',
        'quality_premium_percent',
        'state',
        'district',
        'transaction_date',
        'season',
        'source',
        'listing_id',
        'booking_id',
        'transaction_id',
    ]
    
    relations = {
            'listing': {
                'name': 'listing_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.marketplace_listing', fromlist=['MarketplaceListing']).MarketplaceListing
            },
            'booking': {
                'name': 'booking_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.advance_booking', fromlist=['AdvanceBooking']).AdvanceBooking
            },
            'transaction': {
                'name': 'transaction_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.livestock_transaction', fromlist=['LivestockTransaction']).LivestockTransaction
            },
    }
