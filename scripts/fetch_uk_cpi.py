# -*- coding: utf-8 -*-
"""
fetch_uk_cpi.py - UK CPI Data Fetcher for Inflation Dashboard
==============================================================

Usage:
    python scripts/fetch_uk_cpi.py

Environment Variables Required:
    FRED_API_KEY - Your FRED API key
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_KEY - Your Supabase service role key

Data Source:
    FRED Series: GBRCPIALLMINMEI
    - UK CPI All Items Index (2015=100)
    - Monthly, Not Seasonally Adjusted
    - Original source: OECD -> ONS
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Supabase import (optional - only needed for save_to_supabase)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


# ============================================================
# Configuration
# ============================================================

FRED_API_KEY = os.environ.get("FRED_API_KEY", "c61001ab2426c42a3583e4738770c3df")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# FRED Series for UK CPI
FRED_SERIES_ID = "GBRCPIALLMINMEI"


# ============================================================
# FRED API Functions
# ============================================================

def fetch_uk_cpi_from_fred():
    """
    Fetch UK CPI data from FRED API
    
    Returns:
        {
            "country": "UK",
            "date": "2025-03-01",
            "cpi_index": 136.1,
            "yoy_inflation": 2.8,
            "measure": "headline",
            "source": "FRED (OECD/ONS)"
        }
    """
    base_url = "https://api.stlouisfed.org/fred/series/observations"
    
    # Get last 15 months of data for YoY calculation
    params = {
        "series_id": FRED_SERIES_ID,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 15
    }
    
    print("[UK] Fetching data from FRED (series: {})...".format(FRED_SERIES_ID))
    
    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    observations = data.get("observations", [])
    if not observations:
        raise ValueError("No observations returned from FRED")
    
    # Parse observations
    parsed = []
    for obs in observations:
        date_str = obs["date"]
        value = obs["value"]
        if value != ".":  # FRED uses "." for missing values
            parsed.append({
                "date": date_str,
                "value": float(value)
            })
    
    if len(parsed) < 2:
        raise ValueError("Not enough data points for YoY calculation")
    
    # Latest data point
    latest = parsed[0]
    latest_date = datetime.strptime(latest["date"], "%Y-%m-%d")
    latest_index = latest["value"]
    
    print("[UK] Latest data: {} = {}".format(latest["date"], latest_index))
    
    # Find data from 12 months ago for YoY calculation
    yoy_inflation = None
    target_year = latest_date.year - 1
    target_month = latest_date.month
    
    for obs in parsed:
        obs_date = datetime.strptime(obs["date"], "%Y-%m-%d")
        if obs_date.year == target_year and obs_date.month == target_month:
            year_ago_index = obs["value"]
            yoy_inflation = round(
                ((latest_index - year_ago_index) / year_ago_index) * 100, 2
            )
            print("[UK] YoY calculation: ({} - {}) / {} * 100 = {}%".format(
                latest_index, year_ago_index, year_ago_index, yoy_inflation))
            break
    
    if yoy_inflation is None:
        print("[UK] Warning: Could not find data from 12 months ago for YoY calculation")
    
    return {
        "country": "UK",
        "date": latest["date"],
        "cpi_index": latest_index,
        "yoy_inflation": yoy_inflation,
        "measure": "headline",
        "source": "FRED (OECD/ONS)"
    }


# ============================================================
# Supabase Functions
# ============================================================

def get_supabase_client():
    """Get Supabase client"""
    if not SUPABASE_AVAILABLE:
        raise ImportError("supabase module not installed. Run: pip install supabase")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def save_to_supabase(data, table_name="cpi_data"):
    """
    Save CPI data to Supabase
    Uses UPDATE -> INSERT pattern to avoid duplicates
    
    Args:
        data: CPI data dict from fetch_uk_cpi_from_fred()
        table_name: Supabase table name (default: "cpi_data")
    
    Returns:
        True if successful
    """
    client = get_supabase_client()
    
    record = {
        "country": data["country"],
        "reference_date": data["date"],
        "cpi_index": data["cpi_index"],
        "yoy_inflation": data["yoy_inflation"],
        "measure": data["measure"],
        "source": data["source"],
        "updated_at": datetime.utcnow().isoformat()
    }
    
    print("[UK] Saving to Supabase table '{}'...".format(table_name))
    
    # Try UPDATE first (upsert pattern)
    # Assumes composite key on (country, reference_date)
    try:
        result = client.table(table_name).upsert(
            record,
            on_conflict="country,reference_date"
        ).execute()
        print("[UK] Saved successfully: {} = {} (YoY: {}%)".format(
            data["date"], data["cpi_index"], data["yoy_inflation"]))
        return True
    except Exception as e:
        print("[UK] Supabase error: {}".format(e))
        raise


# ============================================================
# Main Entry Point
# ============================================================

def fetch_uk_cpi():
    """
    Main function to fetch UK CPI data
    Compatible with your existing US/NZ pattern
    
    Returns:
        {
            "country": "UK",
            "date": "2025-03-01",
            "cpi_index": 136.1,
            "yoy_inflation": 2.8,
            "measure": "headline",
            "source": "FRED (OECD/ONS)"
        }
    """
    return fetch_uk_cpi_from_fred()


def main():
    """Main entry point for CLI usage"""
    print("=" * 60)
    print("UK CPI Data Fetcher")
    print("=" * 60)
    
    try:
        # Fetch data
        data = fetch_uk_cpi()
        
        print("")
        print("[Result]")
        print("  Country:       {}".format(data["country"]))
        print("  Date:          {}".format(data["date"]))
        print("  CPI Index:     {}".format(data["cpi_index"]))
        print("  YoY Inflation: {}%".format(data["yoy_inflation"]))
        print("  Source:        {}".format(data["source"]))
        
        # Save to Supabase if configured
        if SUPABASE_URL and SUPABASE_KEY:
            print("")
            print("[Supabase]")
            save_to_supabase(data)
        else:
            print("")
            print("[Supabase] Skipped (credentials not configured)")
        
        print("")
        print("=" * 60)
        print("Done!")
        print("=" * 60)
        
        return data
        
    except Exception as e:
        print("")
        print("[Error] {}".format(e))
        raise


if __name__ == "__main__":
    main()
