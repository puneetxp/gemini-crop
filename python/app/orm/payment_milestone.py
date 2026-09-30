"""
PaymentMilestone ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class PaymentMilestone(Model):
    """PaymentMilestone model for payment_milestones table"""
    
    table = 'payment_milestones'
    
    fillable = [
        'enable',
        'milestone_type',
        'amount',
        'due_date',
        'paid_date',
        'status',
        'payment_method',
        'transaction_id',
        'booking_id',
    ]
    
    relations = {
            'booking': {
                'name': 'booking_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.advance_booking', fromlist=['AdvanceBooking']).AdvanceBooking
            },
    }
