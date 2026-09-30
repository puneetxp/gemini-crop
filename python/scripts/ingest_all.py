#!/usr/bin/env python3
"""
One-shot ingestion runner.

Runs every ingestion source that can run with the current configuration:
  - SLUSI LCC reports + microwatershed maps  (public scrape, no key needed)
  - data.gov.in mandi prices                  (needs DATAGOV_API_KEY)
  - data.gov.in soil moisture                 (needs DATAGOV_MOISTURE_API_KEY)
  - NDAP price CSVs from email                (opt-in: --only mail; Microsoft sign-in
                                               in your browser, Vertex AI for embeddings)

Keys are read from the system_settings table or the environment / .env.
Sources whose key is missing are skipped, not failed.

Usage:
    python scripts/ingest_all.py                      # everything available
    python scripts/ingest_all.py --only slusi
    python scripts/ingest_all.py --state Punjab --district Ludhiana
    python scripts/ingest_all.py --only mail          # local only: needs your sign-in
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.config import get_system_setting
from app.core.database import engine

SOURCES = ("slusi", "prices", "moisture", "mail")
# mail needs a person to finish the Microsoft sign-in, so it only runs when asked for
DEFAULT_SOURCES = ("slusi", "prices", "moisture")


def table_count(table: str) -> int | str:
    try:
        with engine.connect() as conn:
            return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    except Exception:
        return "n/a"


def clear_stale_slusi_runs() -> None:
    """A crashed run leaves status='running' forever and blocks new runs; mark those failed."""
    with engine.begin() as conn:
        n = conn.execute(
            text(
                "UPDATE slusi_ingestion_runs SET status = 'failed', "
                "error_message = 'stale run cleared by ingest_all.py', completed_at = NOW() "
                "WHERE status = 'running' AND started_at < NOW() - INTERVAL '1 hour'"
            )
        ).rowcount
    if n:
        print(f"   cleared {n} stale 'running' SLUSI run(s)")


def run_slusi() -> bool:
    from app.services.slusi_service import SLUSIService

    clear_stale_slusi_runs()
    result = asyncio.run(SLUSIService().run_ingestion())
    print(
        f"   status={result.status} lcc={result.lcc_records_ingested} "
        f"maps={result.maps_ingested}"
    )
    if result.error_message:
        print(f"   error: {result.error_message}")
    return result.status == "success"


def run_prices(state: str | None) -> bool | None:
    key = get_system_setting("DATAGOV_API_KEY")
    if not key:
        print("   skipped: DATAGOV_API_KEY not set (get one at https://www.data.gov.in)")
        return None
    from scripts.fetch_live_api_prices import fetch_and_ingest_live_prices

    return bool(fetch_and_ingest_live_prices(key, state=state, limit=500))


def run_moisture(state: str, district: str) -> bool | None:
    key = get_system_setting("DATAGOV_MOISTURE_API_KEY") or get_system_setting("DATAGOV_API_KEY")
    if not key:
        print("   skipped: DATAGOV_MOISTURE_API_KEY not set")
        return None
    from scripts.fetch_soil_moisture import fetch_and_ingest_soil_moisture

    return bool(fetch_and_ingest_soil_moisture(key, state, district, limit=250))


def has_google_adc() -> bool:
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    return os.path.exists(
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    )


def run_mail() -> bool | None:
    """Pull NDAP CSVs mailed by ndapadm@gmail.com. Never truncates crop_market_data."""
    if not has_google_adc():
        print(
            "   warning: no Google application-default credentials; files will be downloaded\n"
            "   and cached but 0 rows seeded. Fix: gcloud auth application-default login"
        )
    from scripts.fetch_ndap_from_email import acquire_microsoft_token, download_and_process_emails

    token = acquire_microsoft_token()
    if not token:
        print("   failed: Microsoft sign-in did not complete")
        return False
    if download_and_process_emails(token, limit=None, reset_db=False):
        return True
    print("   nothing new: no NDAP emails found, or every mailed file was already ingested")
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all available ingestion sources")
    parser.add_argument("--only", choices=SOURCES, action="append", help="Run just these sources")
    parser.add_argument("--state", default=None, help="State filter for data.gov.in sources")
    parser.add_argument("--district", default="Gurgaon", help="District for soil moisture")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="   %(levelname)s %(name)s: %(message)s")
    selected = args.only or list(DEFAULT_SOURCES)
    moisture_state = args.state or "Haryana"

    tables = {
        "slusi": ["slusi_lcc_reports", "slusi_microwatershed_maps"],
        "prices": ["crop_market_data"],
        "moisture": ["soil_moisture_data"],
        "mail": ["crop_market_data", "ndap_downloaded_files"],
    }
    before = {t: table_count(t) for s in selected for t in tables[s]}

    results = {}
    for source in selected:
        print(f"\n== {source} ==")
        try:
            if source == "slusi":
                results[source] = run_slusi()
            elif source == "prices":
                results[source] = run_prices(args.state)
            elif source == "moisture":
                results[source] = run_moisture(moisture_state, args.district)
            else:
                results[source] = run_mail()
        except Exception as exc:
            print(f"   failed: {exc}")
            results[source] = False

    print("\n== summary ==")
    for source in selected:
        label = {True: "ok", False: "FAILED", None: "skipped"}[results[source]]
        counts = ", ".join(f"{t}: {before[t]} -> {table_count(t)}" for t in tables[source])
        print(f"   {source:<9} {label:<8} {counts}")

    sys.exit(1 if any(r is False for r in results.values()) else 0)


if __name__ == "__main__":
    main()
