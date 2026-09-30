"""
Live Government API Price Fetcher (data.gov.in)
Fetches real-time commodity prices from the official Indian Government Open Data portal (data.gov.in)
and updates the PostgreSQL database.
"""

import sys
import os
import urllib.request
import json
from datetime import datetime

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.orm.crop_market_data import CropMarketData
from app.core.config import get_system_setting

# data.gov.in Agmarknet API endpoint resource ID
API_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL = f"https://api.data.gov.in/resource/{API_RESOURCE_ID}"

def find_field(record, patterns, default=""):
    """
    Search record keys case-insensitively for matches containing any of the patterns.
    """
    record_lower = {str(k).lower().strip(): v for k, v in record.items() if k is not None}
    
    # Try exact matches first
    for pattern in patterns:
        if pattern in record_lower:
            return record_lower[pattern]
            
    # Try partial matches
    for k, v in record_lower.items():
        for pattern in patterns:
            if pattern in k:
                return v
    return default

def fetch_and_ingest_live_prices(api_key, state=None, limit=100):
    """
    Calls the live data.gov.in API to get daily mandi market prices and inserts them.
    """
    # Build request URL with parameters
    url = f"{BASE_URL}?api-key={api_key}&format=json&limit={limit}"
    if state:
        # Encode state name for URL safety
        import urllib.parse
        safe_state = urllib.parse.quote(state)
        url += f"&filters[state]={safe_state}"
        
    print(f"Calling live API: {url.replace(api_key, 'XXXX-API-KEY')} ...")
    
    import urllib.request
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ API Request failed: {e}")
        return False
        
    # Check if records are present
    records = res_data.get("records", [])
    if not records:
        print("⚠️ No records returned from the API. Check if your API key is valid or state matches.")
        return False
        
    print(f"Successfully fetched {len(records)} records from data.gov.in API.")
    
    success_count = 0
    for rec in records:
        try:
            # Map parameters dynamically from varying Government API keys
            state_val = str(find_field(rec, ["state_name", "state", "st_name"], "Unknown")).strip()
            district_val = str(find_field(rec, ["district_name", "district", "dist_name"], "")).strip()
            market_val = str(find_field(rec, ["market", "mandi", "location"], "")).strip()
            crop_name = str(find_field(rec, ["commodity_name", "commodity", "crop_name", "crop", "item_name"], "Unknown")).strip()
            
            # Map price (can be modal, max, min, or average)
            raw_price = find_field(rec, ["modal_price", "price_per_kg", "price", "modal_price_per_quintal", "max_price", "min_price"], 0)
            try:
                price_val = float(raw_price)
                # If price is in quintals (usually > 150), divide by 100 to get per-kg price
                if price_val > 150:
                    price_per_kg = int(price_val / 100)
                else:
                    price_per_kg = int(price_val)
            except ValueError:
                price_per_kg = 0
                
            # Map date (or default to current time)
            date_val = str(find_field(rec, ["arrival_date", "date", "reported_date", "last_updated"], ""))
            if not date_val:
                date_val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            # Map demand level based on price range
            demand_level = "high" if price_per_kg > 40 else ("medium" if price_per_kg > 20 else "low")
            
            price_record = {
                "enable": 1,
                "crop_name": crop_name,
                "state": state_val,
                "district": f"{district_val} ({market_val})" if market_val and district_val != market_val else (district_val or market_val),
                "price_per_kg": price_per_kg,
                "date": date_val,
                "season": "current",
                "yoy_growth": 0,
                "demand_level": demand_level
            }
            
            CropMarketData.create(price_record)
            success_count += 1
        except Exception as e:
            # Skip records that fail to map or insert
            print(f"⚠️ Failed to process record {rec}: {e}")
            pass
            
    print(f"✅ Ingested {success_count} live records into PostgreSQL database.")
    return True

def main():
    print("====================================================")
    print("Live Government API (data.gov.in) Market Price Fetcher")
    print("====================================================")
    
    api_key = get_system_setting("DATAGOV_API_KEY")
    if not api_key:
        print("\n⚠️  No API Key detected in database or environment.")
        print("Register and obtain an API key at: https://www.data.gov.in/ register/ login")
        api_key = input("Enter your data.gov.in API Key: ").strip()
        
    if not api_key:
        print("❌ API Key is required to call the live endpoint.")
        return
        
    state_filter = input("Enter State to filter (optional, e.g., Punjab, Maharashtra): ").strip()
    fetch_and_ingest_live_prices(api_key, state=state_filter if state_filter else None)

if __name__ == "__main__":
    main()
