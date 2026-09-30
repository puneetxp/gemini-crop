"""
TransportBooking ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class TransportBooking(Model):
    """TransportBooking model for transport_bookings table"""
    
    table = 'transport_bookings'
    
    fillable = [
        'enable',
        'pickup_address',
        'pickup_latitude',
        'pickup_longitude',
        'delivery_address',
        'delivery_latitude',
        'delivery_longitude',
        'distance_km',
        'livestock_type',
        'livestock_count',
        'animal_value',
        'transport_cost',
        'insurance_opted',
        'insurance_cost',
        'total_cost',
        'scheduled_pickup_date',
        'estimated_delivery_date',
        'actual_pickup_date',
        'actual_delivery_date',
        'status',
        'tracking_updates',
        'special_instructions',
        'rating',
        'review',
        'reviewed_at',
        'cancelled_at',
        'cancellation_reason',
        'transaction_id',
        'provider_id',
        'requester_id',
    ]
    
    relations = {
            'transaction': {
                'name': 'transaction_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.livestock_transaction', fromlist=['LivestockTransaction']).LivestockTransaction
            },
            'provider': {
                'name': 'provider_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.transport_provider', fromlist=['TransportProvider']).TransportProvider
            },
            'requester': {
                'name': 'requester_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
