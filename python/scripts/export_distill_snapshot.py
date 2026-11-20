#!/usr/bin/env python3
"""
Export a read-only snapshot of the public reference tables that the distillation
notebook (colab/02_tool_distillation_dataset.ipynb) uses as tool data.

Usage (from python/):
    python scripts/export_distill_snapshot.py --out ../colab/snapshot
Then upload the folder to Google Drive at  MyDrive/cropsense/snapshot/

Privacy: only public / reference data is exported. Vet phone / email / WhatsApp
and all user-owned rows (farms, plots, soil tests) are left out. Chat transcripts
from voice_assist_logs are exported only with --with-transcripts (text, task and
language only, no user ids), because they are farmers' own words.
"""

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import DB  # noqa: E402

TABLES = {
    "market_prices": (
        "SELECT item_type, item_name, variety, price_per_unit, quality_grade, state, district, "
        "transaction_date, season, source FROM market_prices ORDER BY transaction_date DESC NULLS LAST LIMIT 50000"
    ),
    "msp_rates": (
        "SELECT crop_name, year, season, msp_per_quintal, msp_per_kg, increase_over_previous, "
        "cost_of_production, return_over_cost_percent, source FROM msp_rates"
    ),
    "pest_disease_data": (
        "SELECT name, type, scientific_name, description, affected_crops, risk_stages, temperature_min, "
        "temperature_max, humidity_min, humidity_max, rainfall_min, severity, organic_treatments, "
        "chemical_treatments, prevention_measures, timing_instructions, data_source FROM pest_disease_data"
    ),
    "veterinarians": (
        "SELECT name, clinic_name, specialization, species_supported, location_state, location_district, "
        "available_now, verified, rating FROM veterinarians"
    ),
}

TRANSCRIPTS_SQL = (
    "SELECT task, ui_lang, language_detected, transcript, intent FROM voice_assist_logs "
    "WHERE transcript IS NOT NULL AND transcript <> '' ORDER BY id DESC LIMIT 20000"
)


def _jsonable(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (bytes, bytearray, memoryview)):
        return None
    return v


def dump(name: str, sql: str, out: Path) -> None:
    try:
        rows = DB.raw(sql, []).result or []
    except Exception as e:  # table missing in this environment
        print(f"  ! {name}: skipped ({e})")
        return
    rows = [{k: _jsonable(v) for k, v in dict(r).items()} for r in rows]
    (out / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(f"  {name}: {len(rows)} rows")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../colab/snapshot")
    ap.add_argument("--with-transcripts", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"Exporting snapshot to {out.resolve()}")
    for name, sql in TABLES.items():
        dump(name, sql, out)
    if args.with_transcripts:
        dump("transcripts", TRANSCRIPTS_SQL, out)
    print("Done. Upload this folder to Drive: MyDrive/cropsense/snapshot/")


if __name__ == "__main__":
    main()
