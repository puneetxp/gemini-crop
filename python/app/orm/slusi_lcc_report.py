"""
SlusiLccReport ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class SlusiLccReport(Model):
    """SlusiLccReport model for slusi_lcc_reports table"""
    
    table = 'slusi_lcc_reports'
    
    fillable = [
        'enable',
        'state',
        'district',
        'report_no',
        'year',
        'total_area_ha',
        'lcc_class_i',
        'lcc_class_ii',
        'lcc_class_iii',
        'lcc_class_iv',
        'lcc_class_v',
        'lcc_class_vi',
        'lcc_class_vii',
        'lcc_class_viii',
        'forest_area',
        'miscellaneous_area',
        'spatial_available',
        'non_spatial_available',
        'ingested_at',
    ]
