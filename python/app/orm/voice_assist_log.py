"""
VoiceAssistLog ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class VoiceAssistLog(Model):
    """VoiceAssistLog model for voice_assist_logs table"""
    
    table = 'voice_assist_logs'
    
    fillable = [
        'enable',
        'source',
        'task',
        'ui_lang',
        'language_detected',
        'mime_type',
        'audio_bytes',
        'duration_ms',
        'transcript',
        'intent',
        'model_used',
        'status',
        'error',
        'latency_ms',
        'user_id',
    ]
    
    relations = {
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
    }
