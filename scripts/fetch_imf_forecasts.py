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
    - docs/data/imf_forecasts.json

No API key required.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Output directory — single source of truth (same convention as fetch_historical_cpi.py)
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "data" if Path(__file__).parent.name == "scripts" else Path("docs/data")

# IMF DataMapper API base URL
IMF_API_BASE = "https://www.imf.org/external/datamapper/api/v1"

# Country mapping: Dashboard code -> IMF code
# Note: Euro Area uses the "EURO" group code (not country code "EMU", which returns empty).
COUNTRY_MAPPING = {
    "US": "USA",
    "EA": "EURO",  # Euro Area — group code, not "EMU"
    "UK": "GBR",
    "CA": "CAN",
    "AU": "AUS",
    "NZ": "NZL",
    "ZA": "ZAF",
    "JP": "JPN",
    "CN": "CHN",
    "IN": "IND",
    "KR": "KOR",
    "SG": "SGP",
    "BR": "BRA",
    "MX": "MEX",
    "VE": "VEN",
}

# Country names for output
COUNTRY_NAMES = {
    "US": "United States",
    "EA": "Euro Area",
    "UK": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "ZA": "South Africa",
    "JP": "Japan",
    "CN": "China",
    "IN": "India",
    "KR": "South Korea",
    "SG": "Singapore",
    "BR": "Brazil",
    "MX": "Mexico",
    "VE": "Venezuela",
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
    
    # Preserve existing 'note' and 'display_order' if the file already exists
    existing_path = OUTPUT_DIR / "imf_forecasts.json"
    existing: Dict = {}
    if existing_path.exists():
        try:
            with open(existing_path, encoding='utf-8') as f:
                existing = json.load(f)
        except (OSError, json.JSONDecodeError):
            existing = {}

    # Build output. Preserve manually curated fields: url, publication_url,
    # note, display_order. (publication_url points at the specific WEO
    # edition page rendered in the dashboard footer — must be refreshed
    # manually on each WEO release.)
    default_url = "https://www.imf.org/external/datamapper/PCPIPCH@WEO"
    result: Dict = {
        "source": "IMF World Economic Outlook",
        "version": weo_version,
        "retrieved": datetime.now().strftime("%Y-%m-%d"),
        "indicator": "PCPIPCH",
        "indicator_label": "Inflation rate, average consumer prices (% change)",
        "url": existing.get("url") or default_url,
    }
    if existing.get("publication_url"):
        result["publication_url"] = existing["publication_url"]
    if existing.get("note"):
        result["note"] = existing["note"]
    if existing.get("display_order"):
        result["display_order"] = existing["display_order"]
    result["countries"] = {}
    
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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

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
