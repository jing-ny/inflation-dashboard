# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

FRED_API_KEY = os.environ.get("FRED_API_KEY")
SERIES_ID = "NZLCPIALLQINMEI"  # NZ CPI All Items (Quarterly)


def fetch_nz_cpi_series(quarters=5):
    """Fetch NZ CPI data from FRED API (quarterly)"""
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not set. Add it to .env.local")
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    
    params = {
        "series_id": SERIES_ID,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": quarters
    }
    
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    observations = data.get("observations", [])
    
    # Filter out missing values (FRED uses "." for missing)
    valid = [obs for obs in observations if obs["value"] != "."]
    
    return valid[:quarters]


def parse_cpi_entry(entry):
    """Parse FRED observation into (date, value)"""
    value = float(entry["value"])
    date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
    return date, value


def compute_yoy(latest, one_year_ago):
    return (latest - one_year_ago) / one_year_ago * 100


if __name__ == "__main__":
    # Get 5 quarters to have current + 4 quarters back (1 year ago)
    data = fetch_nz_cpi_series(5)
    
    latest_date, latest_value = parse_cpi_entry(data[0])
    prev_date, prev_value = parse_cpi_entry(data[4])  # 4 quarters = 1 year
    
    yoy = compute_yoy(latest_value, prev_value)
    
    print("NZ CPI (Headline)")
    print("-----------------")
    print(f"Date           : {latest_date} (Q{(latest_date.month-1)//3 + 1})")
    print(f"CPI Index      : {latest_value:.2f}")
    print(f"YoY Inflation  : {yoy:.2f}%")
    print("Source         : FRED (OECD/Stats NZ)")
    print("Note           : NZ CPI is quarterly, not monthly")
