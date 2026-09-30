"""
NdapDownloadedFile ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class NdapDownloadedFile(Model):
    """NdapDownloadedFile model for ndap_downloaded_files table"""
    
    table = 'ndap_downloaded_files'
    
    fillable = [
        'enable',
        'file_name',
        'file_hash',
        'file_content',
    ]
