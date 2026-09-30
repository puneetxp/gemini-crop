"""
WeatherForecast ORM Model
Auto-generated from JSON schema
"""

from app.core.model import Model


class WeatherForecast(Model):
    """WeatherForecast model for weather_forecasts table"""
    
    table = 'weather_forecasts'
    
    fillable = [
        'enable',
        'latitude',
        'longitude',
        'location_name',
        'state',
        'district',
        'forecast_date',
        'forecast_time',
        'forecast_type',
        'temperature_min',
        'temperature_max',
        'temperature_avg',
        'feels_like',
        'rainfall_probability',
        'rainfall_amount',
        'rainfall_intensity',
        'wind_speed',
        'wind_direction',
        'wind_gust',
        'humidity',
        'pressure',
        'dew_point',
        'cloud_cover',
        'visibility',
        'uv_index',
        'solar_radiation',
        'weather_condition',
        'weather_description',
        'weather_icon',
        'evapotranspiration',
        'soil_moisture_index',
        'growing_degree_days',
        'data_source',
        'source_forecast_id',
        'data_quality_score',
        'fetched_at',
        'expires_at',
    ]
