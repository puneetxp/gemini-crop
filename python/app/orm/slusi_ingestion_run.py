"""
SlusiIngestionRun ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SlusiIngestionRun(Model):
    """SlusiIngestionRun model for slusi_ingestion_runs table"""
    
    table = 'slusi_ingestion_runs'
    
    fillable = [
        'enable',
        'started_at',
        'completed_at',
        'status',
        'lcc_records_ingested',
        'maps_ingested',
        'error_message',
    ]
