"""
UserNotification ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class UserNotification(Model):
    """UserNotification model for user_notifications table"""
    
    table = 'user_notifications'
    
    fillable = [
        'enable',
        'title',
        'message',
        'type',
        'link',
        'data',
        'is_read',
        'read_at',
        'user_id',
    ]
    
    relations = {
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
