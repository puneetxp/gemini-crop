"""
PushSubscription ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class PushSubscription(Model):
    """PushSubscription model for push_subscriptions table"""
    
    table = 'push_subscriptions'
    
    fillable = [
        'enable',
        'user_id',
        'endpoint',
        'p256dh',
        'auth',
        'user_agent',
    ]
