"""
NdapIngestionRun ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class NdapIngestionRun(Model):
    """NdapIngestionRun model for ndap_ingestion_runs table"""
    
    table = 'ndap_ingestion_runs'
    
    fillable = [
        'enable',
        'file_name',
        'file_hash',
        'started_at',
        'completed_at',
        'status',
        'records_ingested',
        'error_message',
    ]
