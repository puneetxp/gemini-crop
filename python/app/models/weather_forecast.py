from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from datetime import date as _date, datetime as _datetime


class WeatherForecast(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    enable: int
    latitude: float
    longitude: float
    location_name: str | None = None
    state: str | None = None
    district: str | None = None
    forecast_date: date
    forecast_time: datetime | None = None
    forecast_type: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    temperature_avg: float | None = None
    feels_like: float | None = None
    rainfall_probability: float | None = None
    rainfall_amount: float | None = None
    rainfall_intensity: str | None = None
    wind_speed: float | None = None
    wind_direction: str | None = None
    wind_gust: float | None = None
    humidity: float | None = None
    pressure: float | None = None
    dew_point: float | None = None
    cloud_cover: float | None = None
    visibility: float | None = None
    uv_index: float | None = None
    solar_radiation: float | None = None
    weather_condition: str | None = None
    weather_description: str | None = None
    weather_icon: str | None = None
    evapotranspiration: float | None = None
    soil_moisture_index: float | None = None
    growing_degree_days: float | None = None
    data_source: str | None = None
    source_forecast_id: str | None = None
    data_quality_score: float | None = None
    fetched_at: datetime | None = None
    expires_at: datetime | None = None


class WeatherForecastInput(BaseModel):
    enable: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None
    state: str | None = None
    district: str | None = None
    forecast_date: _date | None = None
    forecast_time: _datetime | None = None
    forecast_type: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None
    temperature_avg: float | None = None
    feels_like: float | None = None
    rainfall_probability: float | None = None
    rainfall_amount: float | None = None
    rainfall_intensity: str | None = None
    wind_speed: float | None = None
    wind_direction: str | None = None
    wind_gust: float | None = None
    humidity: float | None = None
    pressure: float | None = None
    dew_point: float | None = None
    cloud_cover: float | None = None
    visibility: float | None = None
    uv_index: float | None = None
    solar_radiation: float | None = None
    weather_condition: str | None = None
    weather_description: str | None = None
    weather_icon: str | None = None
    evapotranspiration: float | None = None
    soil_moisture_index: float | None = None
    growing_degree_days: float | None = None
    data_source: str | None = None
    source_forecast_id: str | None = None
    data_quality_score: float | None = None
    fetched_at: _datetime | None = None
    expires_at: _datetime | None = None
