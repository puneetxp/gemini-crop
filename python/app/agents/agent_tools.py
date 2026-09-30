"""
Shared tools for Google Antigravity AI agents in CropSense.
These tools allow the agents to query the primary PostgreSQL database and the OpenWeather/IMD APIs.
"""

import logging
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

from app.core.database import get_db_context
from app.services.farm_access import farm_for_user, fetch_all, fetch_one, plot_for_user
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

# Data access: raw SQL through app.core.db.DB (app/orm classes are not SQLAlchemy models).
# Owner scoping: the tool arguments come from the model/prompt, so they are never trusted. The API
# layer sets the signed-in user with set_agent_user(); farm / plot tools only return that user's
# data (admins: any). With no user set, farm / plot tools return "not found" (fail closed).
_agent_user: ContextVar[Any] = ContextVar("cropsense_agent_user", default=None)


def set_agent_user(user) -> None:
    """Set the signed-in user whose farms / plots the agent tools may read (call before running an agent)."""
    _agent_user.set(user)


def get_farm_details(farm_id: int) -> str:
    """Retrieves metadata for a specific farm (owner user ID, size in acres, location details).

    Args:
        farm_id: The unique ID of the farm.
    """
    try:
        user = _agent_user.get()
        try:
            if user is None:
                raise LookupError("no signed-in user")
            farm = farm_for_user(farm_id, user)
        except LookupError:
            return f"Farm with ID {farm_id} not found."

        # farms columns: location_state / location_district / total_area (+ area_unit) / irrigation_type;
        # there is no pincode column on farms.
        return (
            f"Farm ID: {farm.id}\n"
            f"User ID: {farm.user_id}\n"
            f"State: {farm.location_state}\n"
            f"District: {farm.location_district}\n"
            f"Pincode: {farm.get('pincode')}\n"
            f"Latitude: {farm.latitude}\n"
            f"Longitude: {farm.longitude}\n"
            f"Total Area: {farm.total_area} {farm.area_unit or 'acres'}\n"
            f"Soil Type: {farm.primary_soil_type}\n"
            f"Irrigation: {farm.irrigation_type}\n"
        )
    except Exception as e:
        logger.error(f"Error getting farm details: {e}")
        return f"Error retrieving details for farm {farm_id}: {str(e)}"


def get_soil_info(plot_id: int) -> str:
    """Retrieves the latest soil test results for a specific farm plot.

    Args:
        plot_id: The unique ID of the farm plot.
    """
    try:
        user = _agent_user.get()
        try:
            if user is None:
                raise LookupError("no signed-in user")
            plot = plot_for_user(plot_id, user)
        except LookupError:
            return f"Farm plot with ID {plot_id} not found."

        # soil_test_results columns: plot_id, test_date, *_kg_per_ha, organic_carbon_percent, recommendations
        soil_test = fetch_one(
            "SELECT * FROM soil_test_results WHERE plot_id = ? ORDER BY test_date DESC, id DESC LIMIT 1",
            [plot_id],
        )

        plot_info = f"Plot ID: {plot.id}, Size: {plot.area} acres, Soil Type: {plot.soil_type}\n"
        if not soil_test:
            return plot_info + "No soil test records found for this plot."

        return (
            plot_info + f"Soil Test Date: {soil_test.test_date}\n"
            f"Nitrogen (N): {soil_test.nitrogen_kg_per_ha} kg/ha\n"
            f"Phosphorus (P): {soil_test.phosphorus_kg_per_ha} kg/ha\n"
            f"Potassium (K): {soil_test.potassium_kg_per_ha} kg/ha\n"
            f"pH level: {soil_test.ph_level}\n"
            f"Organic Carbon: {soil_test.organic_carbon_percent}%\n"
            f"Electrical Conductivity: {soil_test.electrical_conductivity} dS/m\n"
            f"Recommendation: {soil_test.recommendations or 'None'}"
        )
    except Exception as e:
        logger.error(f"Error getting soil info: {e}")
        return f"Error retrieving soil info for plot {plot_id}: {str(e)}"


async def get_weather_forecast(latitude: float, longitude: float) -> str:
    """Fetches weather forecast details for agricultural coordinates.

    Args:
        latitude: GPS latitude of the location.
        longitude: GPS longitude of the location.
    """
    try:
        # Use database context to create weather service
        with get_db_context() as db:
            weather_service = WeatherService(db)
            forecast = await weather_service.get_forecast(latitude, longitude)
            if not forecast:
                return "Failed to fetch weather forecast data."

            # Formulate summary
            summary = []
            for day in forecast[:5]:  # Return 5-day forecast
                summary.append(
                    f"Date: {day.get('date')}, Temp: {day.get('min_temp')}°C to {day.get('max_temp')}°C, "
                    f"Rainfall: {day.get('rainfall')}mm, Condition: {day.get('condition')}"
                )
            return "\n".join(summary)
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        return f"Error retrieving weather forecast: {str(e)}"


def get_market_prices(crop_name: str) -> str:
    """Retrieves current market prices and historical price trends for a crop.

    Args:
        crop_name: The name of the crop (e.g. "Rice", "Wheat").
    """
    try:
        # market_prices is a transaction log: item_name / price_per_unit / state / district / transaction_date
        # (no crop_name, market_name, min_price or max_price columns). Public market data, no owner scoping.
        prices = fetch_all(
            """SELECT * FROM market_prices WHERE item_name ILIKE ?
               ORDER BY transaction_date DESC NULLS LAST, id DESC LIMIT 5""",
            ["%" + crop_name.replace("%", "").replace("_", "") + "%"],
        )

        if not prices:
            return f"No price listings found for crop '{crop_name}'."

        summary = []
        for price in prices:
            when = price.transaction_date or price.updated_at
            summary.append(
                f"Market: {price.source or 'N/A'}, State: {price.state}, District: {price.district}, "
                f"Price: Rs.{price.price_per_unit} per unit, "
                f"Date: {when.strftime('%Y-%m-%d') if hasattr(when, 'strftime') else when}"
            )
        return "\n".join(summary)
    except Exception as e:
        logger.error(f"Error getting market prices: {e}")
        return f"Error retrieving market prices: {str(e)}"
