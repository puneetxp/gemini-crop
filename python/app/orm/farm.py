"""
Farm ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class Farm(Model):
    """Farm model for farms table"""
    
    table = 'farms'
    
    fillable = [
        'enable',
        'name',
        'description',
        'location_state',
        'location_district',
        'location_block',
        'location_village',
        'latitude',
        'longitude',
        'total_area',
        'cultivable_area',
        'area_unit',
        'primary_soil_type',
        'soil_ph',
        'soil_characteristics',
        'irrigation_type',
        'water_availability',
        'previous_crops',
        'farming_experience_years',
        'investment_capacity_per_acre',
        'farm_profile_embedding',
        'is_active',
        'is_verified',
        'nitrogen',
        'phosphorus',
        'potassium',
        'ph_level',
        'organic_carbon',
        'electrical_conductivity',
        'sulfur',
        'zinc',
        'iron',
        'boron',
        'copper',
        'manganese',
        'soil_depth_class',
        'slope_class',
        'erosion_class',
        'soil_texture_class',
        'land_capability_class',
        'land_irrigability_class',
        'hydrological_soil_group',
        'shc_data_source',
        'shc_fetched_at',
        'shc_partial_data',
        'shc_unavailable_styles',
        'user_id',
        'owner_id',
    ]
    
    relations = {
            'user': {
                'name': 'user_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
            'owner': {
                'name': 'owner_id',
                'key': 'id',
                'callback': lambda: __import__('app.orm.user', fromlist=['User']).User
            },
            'annual_strategy': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.annual_strategy', fromlist=['AnnualStrategy']).AnnualStrategy
            },
            'farm_plot': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.farm_plot', fromlist=['FarmPlot']).FarmPlot
            },
            'fertilizer_application': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.fertilizer_application', fromlist=['FertilizerApplication']).FertilizerApplication
            },
            'livestock': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.livestock', fromlist=['Livestock']).Livestock
            },
            'marketplace_listing': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.marketplace_listing', fromlist=['MarketplaceListing']).MarketplaceListing
            },
            'pest_disease_alert': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.pest_disease_alert', fromlist=['PestDiseaseAlert']).PestDiseaseAlert
            },
            'satellite_observation': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.satellite_observation', fromlist=['SatelliteObservation']).SatelliteObservation
            },
            'soil_test_result': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.soil_test_result', fromlist=['SoilTestResult']).SoilTestResult
            },
            'weather_alert': {
                'name': 'id',
                'key': 'farm_id',
                'callback': lambda: __import__('app.orm.weather_alert', fromlist=['WeatherAlert']).WeatherAlert
            },
    }
