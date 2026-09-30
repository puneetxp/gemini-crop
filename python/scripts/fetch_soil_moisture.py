#!/usr/bin/env python3
"""
Live Government API Soil Moisture Fetcher (data.gov.in)
Fetches daily soil moisture records for a given state/district and updates the database.
"""

import sys
import os
import urllib.request
import urllib.parse
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add root directory to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.orm.soil_moisture_data import SoilMoistureData
from app.core.config import get_system_setting

# Resource ID for Daily data of Soil Moisture
API_RESOURCE_ID = "4554a3c8-74e3-4f93-8727-8fd92161e345"
BASE_URL = f"https://api.data.gov.in/resource/{API_RESOURCE_ID}"


def fetch_and_ingest_soil_moisture(api_key: str, state: str, district: str, limit: int = 250):
    """
    Queries data.gov.in soil moisture API for given state and district and upserts records.
    """
    # Standardize District for the government API lookup
    api_district = district
    if district.strip().upper() == "GURGAON":
        api_district = "Gurugram"

    # Build request URL
    safe_state = urllib.parse.quote(state.strip())
    safe_district = urllib.parse.quote(api_district.strip())
    
    url = f"{BASE_URL}?api-key={api_key}&format=json&limit={limit}&filters[State]={safe_state}&filters[District]={safe_district}"
    
    print(f"Calling live API for State: {state}, District: {api_district} ...")
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ API Request failed: {e}")
        return False
        
    records = res_data.get("records", [])
    if not records:
        print("⚠️ No soil moisture records returned from the API.")
        return False
        
    print(f"Successfully retrieved {len(records)} records from data.gov.in API.")
    
    success_count = 0
    for rec in records:
        try:
            state_val = str(rec.get("State", "Unknown")).strip()
            # If API returns Gurugram, and the platform has GURGAON, save/normalize appropriately
            district_val = str(rec.get("District", "")).strip()
            if district_val.upper() == "GURUGRAM":
                district_val = "Gurgaon" # Normalize to Gurgaon to match Farm location

            date_str = str(rec.get("Date")).strip()
            moisture_val = float(rec.get("Avg_smlvl_at15cm", 0))
            year_val = int(float(rec.get("Year", datetime.now().year)))
            month_val = str(rec.get("Month", "01")).strip()
            agency_name = str(rec.get("Agency_name", "NRSC VIC MODEL")).strip()
            
            # Upsert by deleting existing state-district-date combination first
            SoilMoistureData.delete({
                "state": state_val,
                "district": district_val,
                "date": date_str
            })
            
            SoilMoistureData.create({
                "enable": 1,
                "state": state_val,
                "district": district_val,
                "date": date_str,
                "year": year_val,
                "month": month_val,
                "moisture_level": moisture_val,
                "agency_name": agency_name
            })
            
            success_count += 1
        except Exception as e:
            print(f"⚠️ Failed to process record {rec}: {e}")
            
    print(f"✅ Ingested {success_count} soil moisture records into database.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Ingest Live Soil Moisture data")
    parser.add_argument("--state", type=str, default="Haryana", help="State name")
    parser.add_argument("--district", type=str, default="Gurgaon", help="District name")
    parser.add_argument("--limit", type=int, default=100, help="Limit number of records")
    args = parser.parse_args()
    
    api_key = get_system_setting("DATAGOV_MOISTURE_API_KEY")
    if not api_key:
        print("❌ DATAGOV_MOISTURE_API_KEY is not configured in database or environment.")
        return
        
    fetch_and_ingest_soil_moisture(api_key, args.state, args.district, args.limit)


if __name__ == "__main__":
    main()
