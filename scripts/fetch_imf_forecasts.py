# -*- coding: utf-8 -*-
"""
Fetch IMF World Economic Outlook Inflation Forecasts
=====================================================

This script fetches inflation forecasts from the IMF DataMapper API
and outputs a JSON file for the dashboard.

API: https://www.imf.org/external/datamapper/api/v1/PCPIPCH
Indicator: PCPIPCH = Inflation rate, average consumer prices (% change)

WEO is released twice per year (April and October).

Usage:
    python fetch_imf_forecasts.py

Output:
    - data/imf_forecasts.json

No API key required.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

# Output directory
OUTPUT_DIR = "data"

# IMF DataMapper API base URL
IMF_API_BASE = "https://www.imf.org/external/datamapper/api/v1"

# Country mapping: Dashboard code -> IMF code
COUNTRY_MAPPING = {
    "US": "USA",
    "CA": "CAN",
    "UK": "GBR",
    "CH": "CHE",
    "DE": "DEU",
    "EA": "EMU",  # Euro Area
    "AU": "AUS",
    "NZ": "NZL",
    "ZA": "ZAF",
    "CN": "CHN"
}

# Country names for output
COUNTRY_NAMES = {
    "US": "United States",
    "CA": "Canada",
    "UK": "United Kingdom",
    "CH": "Switzerland",
    "DE": "Germany",
    "EA": "Euro Area",
    "AU": "Australia",
    "NZ": "New Zealand",
    "ZA": "South Africa",
    "CN": "China"
}


def fetch_imf_forecasts() -> Dict:
    """
    Fetch inflation forecasts from IMF DataMapper API.
    
    Returns dict with structure:
    {
        "source": "IMF World Economic Outlook",
        "version": "October 2025",
        "retrieved": "2026-01-26",
        "indicator": "PCPIPCH",
        "indicator_label": "Inflation rate, average consumer prices",
        "url": "https://www.imf.org/external/datamapper/PCPIPCH@WEO",
        "countries": {
            "US": {
                "name": "United States",
                "imf_code": "USA",
                "forecasts": {
                    "2024": 2.9,
                    "2025": 2.4,
                    "2026": 2.1,
                    ...
                }
            },
            ...
        }
    }
    """
    
    # Get current and next 5 years
    current_year = datetime.now().year
    years = [str(y) for y in range(current_year - 1, current_year + 6)]
    periods = ",".join(years)
    
    # Build country list for API
    imf_codes = list(COUNTRY_MAPPING.values())
    countries_path = "/".join(imf_codes)
    
    # Fetch data
    url = f"{IMF_API_BASE}/PCPIPCH/{countries_path}?periods={periods}"
    print(f"Fetching IMF data from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching IMF data: {e}")
        return None
    
    # Parse response
    values = data.get("values", {}).get("PCPIPCH", {})
    
    # Determine WEO version from current date
    # April release: use "April {year}" if we're past April
    # October release: use "October {year}" if we're past October
    today = datetime.now()
    if today.month >= 10:
        weo_version = f"October {today.year}"
    elif today.month >= 4:
        weo_version = f"April {today.year}"
    else:
        weo_version = f"October {today.year - 1}"
    
    # Build output
    result = {
        "source": "IMF World Economic Outlook",
        "version": weo_version,
        "retrieved": datetime.now().strftime("%Y-%m-%d"),
        "indicator": "PCPIPCH",
        "indicator_label": "Inflation rate, average consumer prices (% change)",
        "url": "https://www.imf.org/external/datamapper/PCPIPCH@WEO",
        "countries": {}
    }
    
    # Map IMF codes back to dashboard codes
    imf_to_dashboard = {v: k for k, v in COUNTRY_MAPPING.items()}
    
    for imf_code, forecasts in values.items():
        dashboard_code = imf_to_dashboard.get(imf_code)
        if dashboard_code:
            # Filter to only include forecast years (current year and beyond)
            forecast_data = {}
            for year, value in forecasts.items():
                if int(year) >= current_year and value is not None:
                    forecast_data[year] = round(value, 1)
            
            if forecast_data:
                result["countries"][dashboard_code] = {
                    "name": COUNTRY_NAMES[dashboard_code],
                    "imf_code": imf_code,
                    "forecasts": forecast_data
                }
    
    return result


def save_json(data: Dict, filename: str):
    """Save data to JSON file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved: {filepath}")


def main():
    print("=" * 60)
    print("IMF World Economic Outlook - Inflation Forecasts")
    print("=" * 60)
    print()
    
    # Fetch IMF forecasts
    imf_data = fetch_imf_forecasts()
    
    if imf_data:
        # Save to JSON
        save_json(imf_data, "imf_forecasts.json")
        
        # Print summary
        print()
        print(f"Source: {imf_data['source']}")
        print(f"Version: {imf_data['version']}")
        print(f"Retrieved: {imf_data['retrieved']}")
        print()
        print("Countries fetched:")
        for code, country_data in imf_data["countries"].items():
            forecasts = country_data["forecasts"]
            years = sorted(forecasts.keys())
            print(f"  {code} ({country_data['name']}): {years[0]}-{years[-1]}")
    else:
        print("Failed to fetch IMF data")
        return 1
    
    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
