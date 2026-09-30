"""SHC WMS Fetcher — fires parallel GetFeatureInfo requests for a farm coordinate."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import cast

import httpx

from app.core.config import settings
from app.schemas.slusi import SHCSoilProfile

logger = logging.getLogger(__name__)

# 7 SRM layers: (code, property_key)
SRM_LAYERS: list[tuple[str, str]] = [
    ("srm_depth", "Soil_Depth"),
    ("srm_slope", "Slope"),
    ("srm_erosion", "Erosion"),
    ("srm_texture", "Texture"),
    ("srm_lcc", "LCC"),
    ("srm_lic", "LIC"),
    ("srm_hsg", "HSG"),
]

# SRM property key → SHCSoilProfile field name
_SRM_FIELD_MAP: dict[str, str] = {
    "Soil_Depth": "soil_depth_class",
    "Slope": "slope_class",
    "Erosion": "erosion_class",
    "Texture": "soil_texture_class",
    "LCC": "land_capability_class",
    "LIC": "land_irrigability_class",
    "HSG": "hydrological_soil_group",
}

# SHC nutrient key → SHCSoilProfile field name
_NUTRIENT_FIELD_MAP: dict[str, str] = {
    "N": "nitrogen",
    "P": "phosphorus",
    "K": "potassium",
    "S": "sulfur",
    "B": "boron",
    "Fe": "iron",
    "Zn": "zinc",
    "Cu": "copper",
    "Mn": "manganese",
    "OC": "organic_carbon",
    "pH": "ph_level",
    "EC": "electrical_conductivity",
}

_UNAVAILABLE_VALUES = {"", "-", "n/a", "na", "null", "none"}


def _is_unavailable(val: object) -> bool:
    if val is None:
        return True
    return str(val).strip().lower() in _UNAVAILABLE_VALUES


class SHCFetcher:
    """Fetches soil data from the SHC WMS API for a given farm coordinate."""

    def __init__(self) -> None:
        self._layers_cache: dict[tuple[int, int], dict[str, object]] = {}

    # ------------------------------------------------------------------
    # BBOX helper
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_bbox(lat: float, lon: float) -> str:
        """Return 'minX,minY,maxX,maxY' centred on (lat, lon) with ±0.005° tile."""
        min_x = lon - 0.005
        max_x = lon + 0.005
        min_y = lat - 0.005
        max_y = lat + 0.005
        return f"{min_x},{min_y},{max_x},{max_y}"

    # ------------------------------------------------------------------
    # Layer discovery
    # ------------------------------------------------------------------

    async def get_district_layers(self, state_code: int, district_code: int) -> dict[str, object]:
        """
        Call /public/layers?state_code=&district_code= to get fixedLayers,
        shcLayers, and district bbox. Result is cached per (state, district).
        """
        cache_key = (state_code, district_code)
        if cache_key in self._layers_cache:
            return self._layers_cache[cache_key]

        url = f"{settings.SHC_WMS_BASE}/public/layers"
        params = {"state_code": state_code, "district_code": district_code}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data: dict[str, object] = resp.json()

        self._layers_cache[cache_key] = data
        return data

    # ------------------------------------------------------------------
    # SRM GetFeatureInfo
    # ------------------------------------------------------------------

    async def fetch_srm_layer(
        self,
        client: httpx.AsyncClient,
        layer_name: str,
        style: str,
        prop_key: str,
        bbox: str,
    ) -> tuple[str, str | None]:
        """
        Fire one SRM GetFeatureInfo request.
        Returns (prop_key, value) or (prop_key, None) on error/empty.
        """
        if not settings.SHC_WMS_PATH:
            return (prop_key, None)

        wms_url = f"{settings.SHC_WMS_BASE}/{settings.SHC_WMS_PATH}"
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": layer_name,
            "QUERY_LAYERS": layer_name,
            "STYLES": style,
            "CRS": "EPSG:4326",
            "BBOX": bbox,
            "WIDTH": "101",
            "HEIGHT": "101",
            "I": "50",
            "J": "50",
            "INFO_FORMAT": "application/json",
            "FEATURE_COUNT": "1",
        }

        try:
            resp = await client.get(wms_url, params=params, timeout=8)
            resp.raise_for_status()
            body = resp.json()
            features = body.get("features", [])
            if not features:
                return (prop_key, None)
            value = features[0].get("properties", {}).get(prop_key)
            if _is_unavailable(value):
                return (prop_key, None)
            return (prop_key, str(value))
        except Exception as exc:
            logger.debug("SRM layer %s failed: %s", layer_name, exc)
            return (prop_key, None)

    # ------------------------------------------------------------------
    # SHC nutrient fetch (1 call → all 12 nutrients)
    # ------------------------------------------------------------------

    async def fetch_shc_nutrients(
        self,
        client: httpx.AsyncClient,
        layer_name: str,
        district_bbox: dict[str, float],
    ) -> dict[str, float | None]:
        """
        Fetch village-level SHC nutrient samples for the district.
        One call with FEATURE_COUNT=100 returns all 12 nutrients per sample.
        Filters zeros (= no data), returns district averages.
        """
        if not settings.SHC_WMS_PATH:
            return {k: None for k in _NUTRIENT_FIELD_MAP}

        wms_url = f"{settings.SHC_WMS_BASE}/{settings.SHC_WMS_PATH}"
        bbox_str = (
            f"{district_bbox['minx']},{district_bbox['miny']},"
            f"{district_bbox['maxx']},{district_bbox['maxy']}"
        )
        params = {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetFeatureInfo",
            "LAYERS": layer_name,
            "QUERY_LAYERS": layer_name,
            "STYLES": "N",
            "CRS": "EPSG:4326",
            "BBOX": bbox_str,
            "WIDTH": "256",
            "HEIGHT": "256",
            "I": "128",
            "J": "128",
            "INFO_FORMAT": "application/json",
            "FEATURE_COUNT": "100",
        }

        try:
            resp = await client.get(wms_url, params=params, timeout=8)
            resp.raise_for_status()
            body = resp.json()
            features = body.get("features", [])
        except Exception as exc:
            logger.debug("SHC nutrient fetch failed for %s: %s", layer_name, exc)
            return {k: None for k in _NUTRIENT_FIELD_MAP}

        # Aggregate non-zero values per nutrient
        sums: dict[str, float] = {}
        counts: dict[str, int] = {}
        for feat in features:
            props = feat.get("properties", {})
            for api_key in _NUTRIENT_FIELD_MAP:
                raw = props.get(api_key)
                if raw is None:
                    continue
                try:
                    val = float(raw)
                except (ValueError, TypeError):
                    continue
                if val == 0.0:
                    continue  # 0 = not collected
                sums[api_key] = sums.get(api_key, 0.0) + val
                counts[api_key] = counts.get(api_key, 0) + 1

        result: dict[str, float | None] = {}
        for api_key in _NUTRIENT_FIELD_MAP:
            if counts.get(api_key, 0) > 0:
                result[api_key] = sums[api_key] / counts[api_key]
            else:
                result[api_key] = None

        return result

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def fetch_soil_profile(
        self,
        lat: float,
        lon: float,
        state_code: int,
        district_code: int,
    ) -> SHCSoilProfile:
        """
        Fire 8 parallel WMS requests (7 SRM + 1 SHC nutrient) and return
        a SHCSoilProfile. Degrades gracefully on partial/full failure.
        """
        if not settings.SHC_WMS_PATH:
            logger.error("SHC_WMS_PATH not configured — returning empty profile")
            return SHCSoilProfile(wms_available=False, partial_data=True)

        # Step 1: discover layers
        try:
            layers_data = await self.get_district_layers(state_code, district_code)
        except Exception as exc:
            logger.error("get_district_layers failed: %s", exc)
            return SHCSoilProfile(wms_available=False, partial_data=True)

        fixed_layers: list[dict[str, str]] = cast(
            list[dict[str, str]], layers_data.get("fixedLayers", [])
        )
        shc_layers: list[str] = cast(list[str], layers_data.get("shcLayers", []))
        bbox_dict: dict[str, float] = cast(dict[str, float], layers_data.get("bbox", {}))

        # Latest SHC cycle = last element (or config default)
        latest_cycle = shc_layers[-1] if shc_layers else settings.SHC_CYCLE
        shc_layer_name = f"{state_code}_{district_code}_shc_{latest_cycle}"

        coord_bbox = self.calculate_bbox(lat, lon)

        # Step 2: fire 8 parallel requests — wrap coroutines in Tasks
        async with httpx.AsyncClient(timeout=12) as client:
            srm_prop_keys: list[str] = []
            srm_tasks: list[asyncio.Task[tuple[str, str | None]]] = []
            for layer in fixed_layers:
                code = layer.get("code", "")
                prop_key = next((p for c, p in SRM_LAYERS if c == code), None)
                if prop_key is None:
                    continue
                srm_prop_keys.append(prop_key)
                srm_tasks.append(
                    asyncio.ensure_future(
                        self.fetch_srm_layer(
                            client,
                            layer["layerName"],
                            layer["style"],
                            prop_key,
                            coord_bbox,
                        )
                    )
                )

            nutrient_task: asyncio.Task[dict[str, float | None]] = asyncio.ensure_future(
                self.fetch_shc_nutrients(client, shc_layer_name, bbox_dict)
            )

            all_tasks: list[asyncio.Task[object]] = [*srm_tasks, nutrient_task]  # type: ignore[list-item]
            done, _ = await asyncio.wait(all_tasks, timeout=10)

        # Step 3: collect results into typed buckets
        str_fields: dict[str, str] = {}
        float_fields: dict[str, float] = {}
        unavailable: list[str] = []

        for task in srm_tasks:
            if task in done:
                prop_key, value = task.result()
                field = _SRM_FIELD_MAP.get(prop_key)
                if field:
                    if value is not None:
                        str_fields[field] = value
                    else:
                        unavailable.append(prop_key)
            else:
                unavailable.append("srm_timeout")

        if nutrient_task in done:
            nutrients = nutrient_task.result()
            for api_key, field in _NUTRIENT_FIELD_MAP.items():
                val = nutrients.get(api_key)
                if val is not None:
                    float_fields[field] = val
                else:
                    unavailable.append(api_key)
        else:
            unavailable.extend(_NUTRIENT_FIELD_MAP.keys())

        all_failed = len(str_fields) == 0 and len(float_fields) == 0
        partial = len(unavailable) > 0

        return SHCSoilProfile(
            # float nutrient fields
            nitrogen=float_fields.get("nitrogen"),
            phosphorus=float_fields.get("phosphorus"),
            potassium=float_fields.get("potassium"),
            sulfur=float_fields.get("sulfur"),
            boron=float_fields.get("boron"),
            iron=float_fields.get("iron"),
            zinc=float_fields.get("zinc"),
            copper=float_fields.get("copper"),
            manganese=float_fields.get("manganese"),
            organic_carbon=float_fields.get("organic_carbon"),
            ph_level=float_fields.get("ph_level"),
            electrical_conductivity=float_fields.get("electrical_conductivity"),
            # string class fields
            soil_depth_class=str_fields.get("soil_depth_class"),
            slope_class=str_fields.get("slope_class"),
            erosion_class=str_fields.get("erosion_class"),
            soil_texture_class=str_fields.get("soil_texture_class"),
            land_capability_class=str_fields.get("land_capability_class"),
            land_irrigability_class=str_fields.get("land_irrigability_class"),
            hydrological_soil_group=str_fields.get("hydrological_soil_group"),
            # metadata
            partial_data=partial,
            wms_available=not all_failed,
            unavailable_styles=unavailable,
            fetched_at=datetime.now(timezone.utc),
        )
