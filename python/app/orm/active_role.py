"""
ActiveRole ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class ActiveRole(Model):
    """ActiveRole model for active_roles table"""
    
    table = 'active_roles'
    
    fillable = [
        'enable',
        'user_id',
        'role_id',
    ]
    
    relations = {
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
            'role': {
                'name': 'role_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.role', fromlist=['Role']).Role
            },
    }
