"""
Crop health from space: Sentinel-2 (ESA Copernicus, 10 m, every ~5 days) for a farm.

Source: Microsoft Planetary Computer (free, no key). Its STAC API finds recent
scenes over the field and its data API computes index statistics over the field
polygon server-side, so no raster libraries are needed here. When the project is
registered for Google Earth Engine, the same readings can come from there
(`source` column) without changing callers.

Per clear scene we keep:
  NDVI = (B08 - B04) / (B08 + B04)  crop vigour / canopy cover
  NDMI = (B08 - B11) / (B08 + B11)  crop water content (low = water stress)
  NDRE = (B8A - B05) / (B8A + B05)  red-edge, sensitive to nitrogen at high canopy
Cloudy scenes are skipped using the scene classification band (SCL), because in
the monsoon a "30 % cloudy" tile can still be fully clouded over one field.

Kept out of satellite_observation_service.py because the generator overwrites that file.
"""

import asyncio
import json
import logging
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.core.db import DB

logger = logging.getLogger(__name__)

STAC_SEARCH = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
DATA_API = "https://planetarycomputer.microsoft.com/api/data/v1/item"
COLLECTION = "sentinel-2-l2a"
SOURCE = "sentinel-2-l2a"

LOOKBACK_DAYS = 120
MAX_SCENES = 10          # scenes checked per refresh
MIN_CLEAR_PCT = 60.0     # share of the field that must be cloud/shadow free
FRESH_DAYS = 5           # re-check the sky at most this often
# SCL classes that are ground we can read: vegetation, bare soil, water, unclassified
CLEAR_CLASSES = {4, 5, 6, 7}

INDICES = {
    "ndvi": "(B08-B04)/(B08+B04)",
    "ndmi": "(B08-B11)/(B08+B11)",
    "ndre": "(B8A-B05)/(B8A+B05)",
}


def field_polygon(lat: float, lon: float, area: Optional[float], unit: Optional[str]) -> Dict[str, Any]:
    """A square the size of the farm around its location (plots have no boundaries yet)."""
    acres = float(area or 2)
    u = (unit or "acres").lower()
    if u.startswith("hect"):
        acres *= 2.471
    elif u.startswith("bigha"):
        acres *= 0.62
    side_m = min(max(math.sqrt(acres * 4046.86), 60.0), 1000.0)
    half = side_m / 2
    dlat = half / 111_320
    dlon = half / (111_320 * max(math.cos(math.radians(lat)), 0.2))
    ring = [[lon - dlon, lat - dlat], [lon + dlon, lat - dlat], [lon + dlon, lat + dlat], [lon - dlon, lat + dlat], [lon - dlon, lat - dlat]]
    return {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [ring]}}


def _bbox(poly: Dict[str, Any]) -> List[float]:
    xs = [p[0] for p in poly["geometry"]["coordinates"][0]]
    ys = [p[1] for p in poly["geometry"]["coordinates"][0]]
    return [min(xs), min(ys), max(xs), max(ys)]


async def _stats(client: httpx.AsyncClient, item: str, params: List, poly: Dict) -> Dict[str, Any]:
    r = await client.post(
        f"{DATA_API}/statistics",
        params=[("collection", COLLECTION), ("item", item), *params],
        content=json.dumps(poly),
        headers={"Content-Type": "application/json"},
    )
    r.raise_for_status()
    return (r.json().get("properties") or {}).get("statistics") or {}


async def _read_scene(client: httpx.AsyncClient, feature: Dict, poly: Dict) -> Optional[Dict[str, Any]]:
    item = feature["id"]
    try:
        scl = await _stats(client, item, [("assets", "SCL"), ("categorical", "true")], poly)
        counts, classes = (next(iter(scl.values())) or {}).get("histogram") or [[], []]
        total = sum(counts) or 0
        clear = sum(c for c, k in zip(counts, classes) if int(k) in CLEAR_CLASSES)
        clear_pct = 100.0 * clear / total if total else 0.0
        if clear_pct < MIN_CLEAR_PCT:
            return {"scene_id": item, "skipped": True, "clear_pct": round(clear_pct, 1)}
        expr = ";".join(INDICES.values())
        vals = await _stats(client, item, [("expression", expr), ("asset_as_band", "true")], poly)
        by_expr = {k: v.get("mean") for k, v in vals.items()}
        reading = {name: by_expr.get(e) for name, e in INDICES.items()}
        return {
            "scene_id": item,
            "observed_on": feature["properties"]["datetime"][:10],
            "clear_pct": round(clear_pct, 1),
            "pixels": int(total),
            **{k: (round(float(v), 3) if v is not None and math.isfinite(float(v)) else None) for k, v in reading.items()},
        }
    except Exception as e:
        logger.warning(f"Sentinel-2 read failed for {item}: {e}")
        return None


async def fetch_observations(poly: Dict[str, Any], days: int = LOOKBACK_DAYS) -> List[Dict[str, Any]]:
    """Clear-sky readings over the field for the last `days`, newest first."""
    end = datetime.now(timezone.utc).date()
    body = {
        "collections": [COLLECTION],
        "bbox": _bbox(poly),
        "datetime": f"{end - timedelta(days=days)}/{end}",
        "limit": MAX_SCENES,
        "query": {"eo:cloud_cover": {"lt": 70}},
        "sortby": [{"field": "properties.datetime", "direction": "desc"}],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(STAC_SEARCH, json=body)
        r.raise_for_status()
        features = r.json().get("features") or []
        sem = asyncio.Semaphore(4)

        async def one(f):
            async with sem:
                return await _read_scene(client, f, poly)

        results = await asyncio.gather(*(one(f) for f in features))
    return [x for x in results if x and not x.get("skipped")]


def _save(farm: Dict[str, Any], readings: List[Dict[str, Any]]) -> None:
    for o in readings:
        DB.raw(
            """INSERT INTO satellite_observations (farm_id, scene_id, observed_on, source, ndvi, ndmi, ndre, clear_pct, pixels, state, district)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (farm_id, scene_id) DO UPDATE SET ndvi = EXCLUDED.ndvi, ndmi = EXCLUDED.ndmi, ndre = EXCLUDED.ndre,
                   clear_pct = EXCLUDED.clear_pct, pixels = EXCLUDED.pixels, updated_at = CURRENT_TIMESTAMP""",
            [farm["id"], o["scene_id"], o["observed_on"], SOURCE, o.get("ndvi"), o.get("ndmi"), o.get("ndre"),
             o.get("clear_pct"), o.get("pixels"), farm.get("location_state"), farm.get("location_district")],
        )


def _stored(farm_id: int, days: int = LOOKBACK_DAYS) -> List[Dict[str, Any]]:
    rows = DB.raw(
        """SELECT scene_id, observed_on, ndvi, ndmi, ndre, clear_pct, pixels, source, updated_at
           FROM satellite_observations WHERE farm_id = ? AND observed_on >= ? ORDER BY observed_on DESC""",
        [farm_id, date.today() - timedelta(days=days)],
    ).result or []
    for r in rows:
        for k in ("ndvi", "ndmi", "ndre", "clear_pct"):
            r[k] = float(r[k]) if r.get(k) is not None else None
        r["observed_on"] = str(r["observed_on"])
    return rows


def interpret(obs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Plain-language reading of the latest clear scene and the trend (codes; the UI translates)."""
    if not obs:
        return {"status": "no_data"}
    latest = obs[0]
    ndvi, ndmi = latest.get("ndvi"), latest.get("ndmi")
    prev = next((o for o in obs[1:] if o.get("ndvi") is not None), None)
    change = round(ndvi - prev["ndvi"], 3) if ndvi is not None and prev else None
    if ndvi is None:
        vigour = "unknown"
    elif ndvi < 0.2:
        vigour = "bare"          # bare soil / just sown / harvested
    elif ndvi < 0.35:
        vigour = "sparse"
    elif ndvi < 0.55:
        vigour = "moderate"
    else:
        vigour = "dense"
    water = None if ndmi is None else ("stress" if ndmi < 0.0 else "low" if ndmi < 0.15 else "ok")
    trend = None if change is None else ("falling" if change <= -0.05 else "rising" if change >= 0.05 else "steady")
    flags = []
    if trend == "falling" and vigour in ("sparse", "moderate"):
        flags.append("check_field")          # losing green cover while it should be growing
    if water in ("stress",) and vigour != "bare":
        flags.append("water_stress")
    days_old = (date.today() - date.fromisoformat(latest["observed_on"])).days
    return {
        "status": "ok",
        "observed_on": latest["observed_on"],
        "days_old": days_old,
        "ndvi": ndvi,
        "ndmi": ndmi,
        "ndre": latest.get("ndre"),
        "vigour": vigour,
        "water": water,
        "trend": trend,
        "ndvi_change": change,
        "flags": flags,
        "scene_id": latest["scene_id"],
    }


def preview_urls(scene_id: str, poly: Dict[str, Any]) -> Dict[str, str]:
    """PNG crops of the field from the data API: true colour and NDVI (red = weak, green = strong)."""
    minx, miny, maxx, maxy = _bbox(poly)
    # A little context around the field
    padx, pady = (maxx - minx) * 0.6, (maxy - miny) * 0.6
    box = f"{minx - padx:.6f},{miny - pady:.6f},{maxx + padx:.6f},{maxy + pady:.6f}"
    base = f"{DATA_API}/bbox/{box}/256x256.png?collection={COLLECTION}&item={scene_id}"
    return {
        "true_color": f"{base}&assets=visual&asset_bidx=visual|1,2,3",
        "ndvi": f"{base}&expression=(B08-B04)/(B08%2BB04)&asset_as_band=true&rescale=-0.1,0.9&colormap_name=rdylgn",
    }


async def farm_health(farm: Dict[str, Any], refresh: bool = False) -> Dict[str, Any]:
    """Readings for one farm (from the table, refreshed from Sentinel-2 when stale)."""
    if farm.get("latitude") is None or farm.get("longitude") is None:
        return {"status": "no_location", "farm_id": farm["id"]}
    poly = field_polygon(float(farm["latitude"]), float(farm["longitude"]), farm.get("cultivable_area") or farm.get("total_area"), farm.get("area_unit"))
    obs = _stored(farm["id"])
    last_check = max((o["updated_at"] for o in obs), default=None)
    stale = not obs or last_check is None or (datetime.now() - last_check).days >= FRESH_DAYS
    error = None
    if refresh or stale:
        try:
            fresh = await fetch_observations(poly)
            if fresh:
                _save(farm, fresh)
                obs = _stored(farm["id"])
        except Exception as e:
            logger.warning(f"Sentinel-2 refresh failed for farm {farm['id']}: {e}")
            error = str(e)[:300]
    summary = interpret(obs)
    return {
        "farm_id": farm["id"],
        "source": "Sentinel-2 L2A (ESA Copernicus) via Microsoft Planetary Computer",
        "field": poly,
        "summary": summary,
        "observations": [{k: o[k] for k in ("observed_on", "ndvi", "ndmi", "ndre", "clear_pct")} for o in obs][:12],
        "images": preview_urls(summary["scene_id"], poly) if summary.get("scene_id") else None,
        "error": error,
    }
