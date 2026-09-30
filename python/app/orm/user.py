"""
User ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class User(Model):
    """User model for users table"""
    
    table = 'users'
    
    fillable = [
        'enable',
        'cognito_user_id',
        'firebase_id',
        'username',
        'name',
        'email',
        'phone',
        'google_id',
        'facebook_id',
        'password',
        'user_type',
        'preferred_language',
        'mfa_enabled',
        'latitude',
        'longitude',
        'pincode',
        'state',
        'district',
        'village',
        'address_line',
        'is_active',
        'is_verified',
    ]
    
    relations = {
            'active_role': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.active_role', fromlist=['ActiveRole']).ActiveRole
            },
            'ai_usage_quota': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.ai_usage_quota', fromlist=['AiUsageQuota']).AiUsageQuota
            },
            'crop_diagnosis': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.crop_diagnosis', fromlist=['CropDiagnosis']).CropDiagnosis
            },
            'farm': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.farm', fromlist=['Farm']).Farm
            },
            'livestock_roi_prediction': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.livestock_roi_prediction', fromlist=['LivestockRoiPrediction']).LivestockRoiPrediction
            },
            'transport_provider': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.transport_provider', fromlist=['TransportProvider']).TransportProvider
            },
            'user_notification': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.user_notification', fromlist=['UserNotification']).UserNotification
            },
            'voice_assist_log': {
                'name': 'id',
                'key': 'user_id',
                'callback': lambda: __import__('app.orm.voice_assist_log', fromlist=['VoiceAssistLog']).VoiceAssistLog
            },
    }
