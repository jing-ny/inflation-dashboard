# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

FRED_API_KEY = os.environ.get("FRED_API_KEY")
SERIES_ID = "ZAFCPIALLMINMEI"  # South Africa CPI All Items (Monthly, 2015=100)


def fetch_za_cpi_series(months=13):
    """Fetch South Africa CPI data from FRED API"""
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not set. Add it to .env.local")
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    
    params = {
        "series_id": SERIES_ID,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": months
    }
    
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    observations = data.get("observations", [])
    
    # Filter out missing values (FRED uses "." for missing)
    valid = [obs for obs in observations if obs["value"] != "."]
    
    return valid[:months]


def parse_cpi_entry(entry):
    """Parse FRED observation into (date, value)"""
    value = float(entry["value"])
    date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
    return date, value


def compute_yoy(latest, one_year_ago):
    return (latest - one_year_ago) / one_year_ago * 100


if __name__ == "__main__":
    data = fetch_za_cpi_series(13)
    
    latest_date, latest_value = parse_cpi_entry(data[0])
    prev_date, prev_value = parse_cpi_entry(data[12])
    
    yoy = compute_yoy(latest_value, prev_value)
    
    print("ZA CPI (Headline)")
    print("-----------------")
    print(f"Date           : {latest_date}")
    print(f"CPI Index      : {latest_value:.2f}")
    print(f"YoY Inflation  : {yoy:.2f}%")
    print("Source         : FRED (OECD/Stats SA)")
