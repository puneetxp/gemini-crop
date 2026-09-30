"""
Role ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class Role(Model):
    """Role model for roles table"""
    
    table = 'roles'
    
    fillable = [
        'enable',
        'name',
    ]
    
    relations = {
            'active_role': {
                'name': 'id',
                'key': 'role_id',
                'callback': lambda: __import__('app.orm.active_role', fromlist=['ActiveRole']).ActiveRole
            },
    }
