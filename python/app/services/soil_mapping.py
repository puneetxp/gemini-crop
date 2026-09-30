import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Constants for common soil characteristics based on India Soil Map
# Each soil type gets a default set of parameters (NPK, pH, etc.)
# Note: These are rough defaults intended to be overwritten by proper Soil Tests
SOIL_DEFAULTS = {
    "Alluvial": {
        "primary_soil_type": "loamy",
        "ph_level": 7.5,
        "nitrogen": 40.0,
        "phosphorus": 20.0,
        "potassium": 25.0,
        "organic_carbon": 0.5,
        "electrical_conductivity": 0.8,
        "sulfur": 10.0,
        "zinc": 0.8,
        "iron": 5.0,
        "boron": 0.5,
    },
    "Black": {
        "primary_soil_type": "clay",
        "ph_level": 7.8,
        "nitrogen": 30.0,
        "phosphorus": 15.0,
        "potassium": 45.0,
        "organic_carbon": 0.6,
        "electrical_conductivity": 1.0,
        "sulfur": 12.0,
        "zinc": 0.5,
        "iron": 4.0,
        "boron": 0.4,
    },
    "Red": {
        "primary_soil_type": "sandy",
        "ph_level": 6.0,
        "nitrogen": 25.0,
        "phosphorus": 10.0,
        "potassium": 15.0,
        "organic_carbon": 0.3,
        "electrical_conductivity": 0.5,
        "sulfur": 8.0,
        "zinc": 0.4,
        "iron": 8.0,
        "boron": 0.3,
    },
    "Laterite": {
        "primary_soil_type": "mixed",
        "ph_level": 5.5,
        "nitrogen": 20.0,
        "phosphorus": 8.0,
        "potassium": 10.0,
        "organic_carbon": 0.4,
        "electrical_conductivity": 0.3,
        "sulfur": 6.0,
        "zinc": 0.3,
        "iron": 12.0,
        "boron": 0.2,
    },
    "Desert": {
        "primary_soil_type": "sandy",
        "ph_level": 8.2,
        "nitrogen": 15.0,
        "phosphorus": 12.0,
        "potassium": 30.0,
        "organic_carbon": 0.1,
        "electrical_conductivity": 1.5,
        "sulfur": 5.0,
        "zinc": 0.2,
        "iron": 3.0,
        "boron": 0.6,
    },
    "Mountain": {
        "primary_soil_type": "loamy",
        "ph_level": 6.5,
        "nitrogen": 45.0,
        "phosphorus": 18.0,
        "potassium": 20.0,
        "organic_carbon": 1.2,
        "electrical_conductivity": 0.4,
        "sulfur": 15.0,
        "zinc": 0.6,
        "iron": 6.0,
        "boron": 0.4,
    },
}

# General state-to-soil mapping based on India Soil Map
# The map shows dominant soil types per state
STATE_TO_SOIL = {
    "Punjab": "Alluvial",
    "Haryana": "Alluvial",
    "Uttar Pradesh": "Alluvial",
    "Bihar": "Alluvial",
    "West Bengal": "Alluvial",
    "Assam": "Alluvial",
    "Delhi": "Alluvial",
    "Rajasthan": "Desert",
    "Maharashtra": "Black",
    "Madhya Pradesh": "Black",
    "Gujarat": "Black",  # Gujarat has parts Black, parts Alluvial
    "Telangana": "Black",
    "Odisha": "Red",  # Includes Red and Mixed Red & Black
    "Chhattisgarh": "Red",
    "Jharkhand": "Red",
    "Andhra Pradesh": "Red",
    "Tamil Nadu": "Red",
    "Kerala": "Laterite",
    "Goa": "Laterite",
    "Karnataka": "Red",  # Mixed Red, Black and Laterite
    "Jammu and Kashmir": "Mountain",
    "Jammu & Kashmir": "Mountain",
    "Ladakh": "Mountain",
    "Himachal Pradesh": "Mountain",
    "Uttarakhand": "Mountain",
    "Sikkim": "Mountain",
    "Arunachal Pradesh": "Mountain",
    "Meghalaya": "Mountain",
    "Nagaland": "Mountain",
    "Manipur": "Mountain",
    "Mizoram": "Mountain",
    "Tripura": "Mountain",
}


class SoilMappingService:
    """Service to map geographical locations in India to likely soil profiles"""

    @staticmethod
    def get_likely_soil_profile(state: str, district: str = None) -> Dict[str, Any]:
        """
        Estimate soil profile based on state (and optionally district).
        Returns basic NPK, pH, and soil type defaults based on the India Soil Map.
        """
        if not state:
            return {}

        # Standardize state name representation (capitalization)
        clean_state = str(state).strip().title()

        # Override for specific edge cases
        if clean_state == "Jammu & Kashmir" or clean_state == "Jammu And Kashmir":
            clean_state = "Jammu and Kashmir"

        # District-specific overrides
        if (
            clean_state == "Haryana"
            and district
            and str(district).strip().upper() in ["GURGAON", "GURUGRAM"]
        ):
            return {
                "primary_soil_type": "sandy loam",
                "ph_level": 7.2,
                "nitrogen": 35.0,
                "phosphorus": 18.0,
                "potassium": 22.0,
                "organic_carbon": 0.45,
                "electrical_conductivity": 0.7,
                "sulfur": 9.0,
                "zinc": 0.7,
                "iron": 4.5,
                "boron": 0.4,
            }

        # Get dominant soil type for the state
        dominant_soil = STATE_TO_SOIL.get(clean_state)

        if not dominant_soil:
            logger.info(f"Could not map state '{state}' to a known soil type.")
            return {}

        return SOIL_DEFAULTS.get(dominant_soil, {})
