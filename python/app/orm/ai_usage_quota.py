"""
AiUsageQuota ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class AiUsageQuota(Model):
    """AiUsageQuota model for ai_usage_quota table"""
    
    table = 'ai_usage_quota'
    
    fillable = [
        'enable',
        'date',
        'gps_enhanced_requests',
        'pincode_requests',
        'last_reset',
        'quota_limit',
        'user_id',
    ]
    
    relations = {
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
