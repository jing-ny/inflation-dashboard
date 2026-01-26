#!/usr/bin/env python3
"""
Quick test script to verify:
1. Japan FRED series returns current data (not June 2021)
2. IMF API returns forecast data

Run: python3 test_data_sources.py
"""

import requests
import os
from datetime import datetime

# Load FRED API key
FRED_API_KEY = os.environ.get("FRED_API_KEY")

def test_japan_series():
    """Test that Japan series returns recent data."""
    print("=" * 60)
    print("TEST 1: Japan CPI Series (JPNCPALTT01GYM659N)")
    print("=" * 60)
    
    if not FRED_API_KEY:
        print("ERROR: FRED_API_KEY not set")
        return False
    
    series_id = "JPNCPALTT01GYM659N"
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 5
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        observations = data.get("observations", [])
        if not observations:
            print("ERROR: No observations returned")
            return False
        
        print(f"\nLatest 5 observations:")
        print("-" * 40)
        for obs in observations:
            print(f"  {obs['date']}: {obs['value']}%")
        
        # Check if latest date is recent (within last 6 months)
        latest_date = datetime.strptime(observations[0]['date'], "%Y-%m-%d")
        months_ago = (datetime.now() - latest_date).days / 30
        
        if months_ago < 6:
            print(f"\n✅ SUCCESS: Latest data is from {observations[0]['date']} ({months_ago:.1f} months ago)")
            return True
        else:
            print(f"\n❌ WARNING: Latest data is {months_ago:.1f} months old")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_imf_api():
    """Test that IMF API returns forecast data."""
    print("\n" + "=" * 60)
    print("TEST 2: IMF DataMapper API (PCPIPCH)")
    print("=" * 60)
    
    url = "https://www.imf.org/external/datamapper/api/v1/PCPIPCH/USA/JPN?periods=2025,2026,2027"
    
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        values = data.get("values", {}).get("PCPIPCH", {})
        
        if not values:
            print("ERROR: No values returned")
            return False
        
        print(f"\nForecasts returned:")
        print("-" * 40)
        for country, forecasts in values.items():
            print(f"\n  {country}:")
            for year, value in sorted(forecasts.items()):
                if value is not None:
                    print(f"    {year}: {value:.1f}%")
        
        print(f"\n✅ SUCCESS: IMF API working")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    print("\nData Source Verification")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    japan_ok = test_japan_series()
    imf_ok = test_imf_api()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Japan FRED series: {'✅ PASS' if japan_ok else '❌ FAIL'}")
    print(f"  IMF API:           {'✅ PASS' if imf_ok else '❌ FAIL'}")
    print()
    
    return 0 if (japan_ok and imf_ok) else 1


if __name__ == "__main__":
    exit(main())
