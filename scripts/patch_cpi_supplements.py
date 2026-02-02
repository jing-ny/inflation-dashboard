#!/usr/bin/env python3
"""
Patch historical_cpi.json with supplemental data for countries where FRED lags.

This script reads the existing historical_cpi.json and cpi_supplements.json,
merges them, and outputs an updated file.

Usage:
    python patch_cpi_supplements.py

Run this after fetch_historical_cpi.py to add recent data for lagging countries.
"""

import json
import os
from datetime import date

# Paths
HISTORICAL_CPI_FILE = "docs/data/historical_cpi.json"
SUPPLEMENTS_FILE = "docs/data/cpi_supplements.json"
OUTPUT_FILE = "docs/data/historical_cpi.json"

def load_json(filepath):
    """Load JSON file if it exists."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def patch_historical_data():
    """Merge supplement data into historical CPI."""
    
    # Load existing data
    historical = load_json(HISTORICAL_CPI_FILE)
    supplements = load_json(SUPPLEMENTS_FILE)
    
    if not historical:
        print(f"Error: {HISTORICAL_CPI_FILE} not found")
        return
    
    if not supplements:
        print(f"Warning: {SUPPLEMENTS_FILE} not found, nothing to patch")
        return
    
    # Process each country in supplements
    for country_code, supplement_data in supplements.items():
        if country_code.startswith("_"):
            continue  # Skip metadata fields
            
        if country_code not in historical:
            print(f"Warning: {country_code} not in historical data, skipping")
            continue
        
        print(f"\nPatching {country_code}...")
        
        country_historical = historical[country_code]
        history = country_historical.get("history", [])
        
        # Get existing dates for quick lookup
        existing_dates = {item["date"] for item in history}
        
        # Add supplement data
        added_count = 0
        for item in supplement_data.get("supplements", []):
            if item["date"] not in existing_dates:
                history.append(item)
                added_count += 1
                print(f"  Added: {item['date']} = {item['value']}%")
        
        # Sort by date
        history.sort(key=lambda x: x["date"])
        
        # Update latest and previous
        if len(history) >= 2:
            country_historical["latest"] = {
                "date": history[-1]["date"],
                "value": history[-1]["value"]
            }
            country_historical["previous"] = {
                "date": history[-2]["date"],
                "value": history[-2]["value"]
            }
        
        country_historical["history"] = history
        historical[country_code] = country_historical
        
        print(f"  Added {added_count} new data points")
        print(f"  Latest: {country_historical['latest']['date']} = {country_historical['latest']['value']}%")
    
    # Update metadata
    if "_metadata" not in historical:
        historical["_metadata"] = {}
    historical["_metadata"]["last_patched"] = date.today().isoformat()
    historical["_metadata"]["patched_countries"] = [
        k for k in supplements.keys() if not k.startswith("_")
    ]
    
    # Save updated data
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(historical, f, indent=2)
    
    print(f"\n✅ Saved patched data to {OUTPUT_FILE}")

if __name__ == "__main__":
    patch_historical_data()
