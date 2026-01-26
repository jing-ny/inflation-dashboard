#!/usr/bin/env python3
"""
Inflation Dashboard - Central Bank Forecasts Fetcher

Fetches inflation forecasts from central banks and outputs cb_forecasts.json.
This is the SINGLE SOURCE OF TRUTH for all forecast data displayed on the dashboard.

Data Sources:
- US (Fed):  FRED API - FOMC SEP (Summary of Economic Projections)
- EA (ECB):  ECB Data Portal - Macroeconomic Projection Database (MPD)
- UK (BoE):  Manual entry (no reliable API for MPR forecasts)
- AU (RBA):  RBA Historical Forecasts database
- CA (BoC):  Manual entry (no reliable API for MPR forecasts)
- NZ (RBNZ): Manual entry (no reliable API for MPS forecasts)
- ZA (SARB): Manual entry (no reliable API for MPC forecasts)
- CN:        IMF WEO (China doesn't publish official multi-year forecasts)

Usage:
    python fetch_cb_forecasts.py                    # Fetch all available, use cached manual
    python fetch_cb_forecasts.py --update-manual    # Interactive mode to update manual entries
    python fetch_cb_forecasts.py --force            # Force refresh all data

Output:
    data/cb_forecasts.json

Author: Inflation Dashboard Project
Last Updated: 2026-01-26
"""

import os
import sys
import json
import argparse
from datetime import datetime, date
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = "data/cb_forecasts.json"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# FRED Series IDs for FOMC SEP
FRED_SERIES = {
    "PCE_MEDIAN": "PCECTPIMD",      # PCE inflation median projections
    "CORE_PCE_MEDIAN": "JCXFEMD",   # Core PCE inflation median
    "FED_FUNDS_MEDIAN": "FEDTARMD", # Fed funds rate median
}

# ECB MPD API endpoint
ECB_API_BASE = "https://data.ecb.europa.eu/data-detail-api/MPD"

# RBA Forecasts URL
RBA_FORECASTS_URL = "https://www.rba.gov.au/statistics/historical-forecasts.html"

# ============================================================
# MANUAL FORECAST DATA
# ============================================================
# For central banks without APIs, we store the latest forecasts here.
# These should be updated after each major monetary policy meeting.
# The script will use these values when APIs are unavailable.

MANUAL_FORECASTS = {
    "US": {
        # Updated from FOMC December 2025 SEP
        "last_updated": "2025-12-10",
        "source": "FOMC",
        "source_full": "Federal Reserve (FOMC SEP)",
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20251210.htm",
        "publication_date": "December 2025",
        "forecast_type": "PCE Projections",
        "measure": "PCE inflation",
        "projections": {
            "2025": 2.8,
            "2026": 2.4,
            "2027": 2.1,
            "longer_run": 2.0
        },
        "key_quote": "Core inflation 2.5% in 2026, expects only 1 rate cut",
        "note": "PCE inflation (Fed's preferred measure), median projections",
        "policy_rate": {
            "rate": "4.25-4.50%",
            "name": "Fed Funds Rate",
            "last_change": "↓ 25bp Dec 2025"
        }
    },
    "EA": {
        # Updated from ECB December 2025 Staff Projections
        "last_updated": "2025-12-18",
        "source": "ECB",
        "source_full": "European Central Bank (Staff Projections)",
        "source_url": "https://www.ecb.europa.eu/press/projections/html/index.en.html",
        "publication_date": "December 2025",
        "forecast_type": "Staff Projections",
        "measure": "HICP inflation",
        "projections": {
            "2025": 2.1,
            "2026": 1.9,
            "2027": 1.8,
            "2028": 2.0
        },
        "key_quote": "Below target in 2026-27, returns to 2% in 2028",
        "note": "HICP inflation, December 2025 Eurosystem staff projections",
        "policy_rate": {
            "rate": "3.15%",
            "name": "Main Refinancing Rate",
            "last_change": "— held"
        }
    },
    "UK": {
        # Updated from BoE November 2025 MPR
        "last_updated": "2025-11-07",
        "source": "BoE",
        "source_full": "Bank of England (MPR)",
        "source_url": "https://www.bankofengland.co.uk/monetary-policy-report/2025/november-2025",
        "publication_date": "November 2025",
        "forecast_type": "MPC Projections",
        "measure": "CPI inflation",
        "projections": {
            "2025": 3.8,
            "2026": 2.5,
            "2027": 1.9
        },
        "key_quote": "Inflation judged to have peaked, below 2% by Q2 2027",
        "note": "CPI inflation, modal projections from November 2025 MPR",
        "policy_rate": {
            "rate": "4.75%",
            "name": "Bank Rate",
            "last_change": "↓ 25bp Nov 2025"
        }
    },
    "AU": {
        # Updated from RBA November 2025 SMP
        "last_updated": "2025-11-05",
        "source": "RBA",
        "source_full": "Reserve Bank of Australia (SMP)",
        "source_url": "https://www.rba.gov.au/publications/smp/2025/nov/",
        "publication_date": "November 2025",
        "forecast_type": "SMP Forecasts",
        "measure": "Trimmed mean inflation",
        "projections": {
            "2025": 3.2,
            "2026": 2.7,
            "2027": 2.6
        },
        "key_quote": "Above 3% until mid-2026, target by late 2027",
        "note": "Trimmed mean inflation (underlying), November 2025 SMP",
        "policy_rate": {
            "rate": "3.60%",
            "name": "Cash Rate",
            "last_change": "— held"
        }
    },
    "CA": {
        # Updated from BoC October 2025 MPR
        "last_updated": "2025-10-23",
        "source": "BoC",
        "source_full": "Bank of Canada (MPR)",
        "source_url": "https://www.bankofcanada.ca/2025/10/mpr-2025-10-23/",
        "publication_date": "October 2025",
        "forecast_type": "MPR Projections",
        "measure": "CPI inflation",
        "projections": {
            "2025": 2.4,
            "2026": 2.0,
            "2027": 2.0
        },
        "key_quote": "Weaker demand to offset tariff price pressures",
        "note": "CPI inflation, from Monetary Policy Report",
        "policy_rate": {
            "rate": "3.25%",
            "name": "Policy Rate",
            "last_change": "↓ 50bp Oct 2025"
        }
    },
    "NZ": {
        # Updated from RBNZ November 2025 MPS
        "last_updated": "2025-11-27",
        "source": "RBNZ",
        "source_full": "Reserve Bank of New Zealand (MPS)",
        "source_url": "https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement/mps-november-2025",
        "publication_date": "November 2025",
        "forecast_type": "MPS Projections",
        "measure": "CPI inflation",
        "projections": {
            "2025": 3.0,
            "2026": 2.0,
            "2027": 2.0
        },
        "key_quote": "Spare capacity, expect 2% by mid-2026",
        "note": "CPI inflation, November 2025 MPS",
        "policy_rate": {
            "rate": "4.25%",
            "name": "OCR",
            "last_change": "↓ 50bp Nov 2025"
        }
    },
    "ZA": {
        # Updated from SARB November 2025 MPC Statement
        "last_updated": "2025-11-21",
        "source": "SARB",
        "source_full": "South African Reserve Bank (MPC)",
        "source_url": "https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2025/mpc-november-2025",
        "publication_date": "November 2025",
        "forecast_type": "MPC Projections",
        "measure": "CPI inflation",
        "projections": {
            "2025": 3.3,
            "2026": 3.5,
            "2027": 3.1
        },
        "key_quote": "On track to deliver new 3% target over medium term",
        "note": "CPI inflation, November 2025 MPC statement",
        "policy_rate": {
            "rate": "7.75%",
            "name": "Repo Rate",
            "last_change": "↓ 25bp Nov 2025"
        }
    },
    "CN": {
        # China doesn't publish official forecasts - use IMF
        "last_updated": "2025-12-01",
        "source": "IMF",
        "source_full": "IMF Staff Projections",
        "source_url": "https://www.imf.org/en/Publications/WEO",
        "publication_date": "December 2025",
        "forecast_type": "IMF Projections",
        "measure": "CPI inflation",
        "projections": {
            "2025": 0.0,
            "2026": 0.8,
            "2027": None  # Not available
        },
        "key_quote": "Deflationary pressures amid weak domestic demand",
        "note": "PBOC does not publish official forecasts; IMF projections used",
        "policy_rate": {
            "rate": "3.10%",
            "name": "LPR (1Y)",
            "last_change": "— accommodative"
        }
    }
}

# Country metadata (static, rarely changes)
COUNTRY_METADATA = {
    "US": {"country_name": "United States", "flag": "🇺🇸", "central_bank": "Federal Reserve"},
    "EA": {"country_name": "Euro Area", "flag": "🇪🇺", "central_bank": "European Central Bank"},
    "UK": {"country_name": "United Kingdom", "flag": "🇬🇧", "central_bank": "Bank of England"},
    "AU": {"country_name": "Australia", "flag": "🇦🇺", "central_bank": "Reserve Bank of Australia"},
    "CA": {"country_name": "Canada", "flag": "🇨🇦", "central_bank": "Bank of Canada"},
    "NZ": {"country_name": "New Zealand", "flag": "🇳🇿", "central_bank": "Reserve Bank of New Zealand"},
    "ZA": {"country_name": "South Africa", "flag": "🇿🇦", "central_bank": "South African Reserve Bank"},
    "CN": {"country_name": "China", "flag": "🇨🇳", "central_bank": "People's Bank of China"},
}

DISPLAY_ORDER = ["US", "EA", "UK", "CA", "AU", "NZ", "ZA", "CN"]

# ============================================================
# API FETCHERS
# ============================================================

def fetch_fred_series(series_id: str) -> Optional[Dict]:
    """Fetch a series from FRED API."""
    if not FRED_API_KEY:
        print(f"  Warning: FRED_API_KEY not set, skipping FRED fetch")
        return None
    
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=10"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            return data.get("observations", [])
    except urllib.error.URLError as e:
        print(f"  Error fetching FRED series {series_id}: {e}")
        return None


def fetch_fomc_sep() -> Optional[Dict]:
    """
    Fetch FOMC Summary of Economic Projections from FRED.
    Returns the latest PCE inflation projections.
    """
    print("Fetching FOMC SEP from FRED...")
    
    observations = fetch_fred_series(FRED_SERIES["PCE_MEDIAN"])
    if not observations:
        return None
    
    # FRED returns projections for future years
    # Parse the observations to extract year -> value
    projections = {}
    for obs in observations:
        try:
            year = obs.get("date", "")[:4]
            value = float(obs.get("value", ""))
            if year and value:
                projections[year] = value
        except (ValueError, TypeError):
            continue
    
    if projections:
        print(f"  Found FOMC projections: {projections}")
        return projections
    
    return None


def fetch_ecb_mpd() -> Optional[Dict]:
    """
    Fetch ECB Macroeconomic Projection Database.
    Returns HICP inflation projections for Euro Area.
    """
    print("Fetching ECB MPD...")
    
    # ECB SDMX API for inflation projections
    # Series: MPD.A.U2.N.XDC.HICP.PCH.T+0.F (HICP, annual change, forecast)
    url = "https://data.ecb.europa.eu/data-detail-api/MPD.A.U2.N.XDC.HICP.PCH.T+0.F?format=json"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            # Parse ECB response format
            projections = {}
            # ECB API returns data in a specific structure
            if "data" in data:
                for item in data.get("data", []):
                    period = item.get("TIME_PERIOD", "")
                    value = item.get("OBS_VALUE")
                    if period and value:
                        projections[period] = float(value)
            
            if projections:
                print(f"  Found ECB projections: {projections}")
                return projections
                
    except urllib.error.URLError as e:
        print(f"  Error fetching ECB MPD: {e}")
    except json.JSONDecodeError as e:
        print(f"  Error parsing ECB response: {e}")
    
    return None


def fetch_imf_weo(country_code: str = "CHN") -> Optional[Dict]:
    """
    Fetch IMF World Economic Outlook projections.
    Uses the same approach as fetch_imf_forecasts.py
    """
    print(f"Fetching IMF WEO for {country_code}...")
    
    # IMF DataMapper API
    url = f"https://www.imf.org/external/datamapper/api/v1/PCPIPCH/{country_code}"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            
            values = data.get("values", {}).get("PCPIPCH", {}).get(country_code, {})
            
            # Get projections for future years
            current_year = datetime.now().year
            projections = {}
            for year_str, value in values.items():
                try:
                    year = int(year_str)
                    if year >= current_year and value is not None:
                        projections[year_str] = round(float(value), 1)
                except (ValueError, TypeError):
                    continue
            
            if projections:
                print(f"  Found IMF projections: {projections}")
                return projections
                
    except urllib.error.URLError as e:
        print(f"  Error fetching IMF WEO: {e}")
    except json.JSONDecodeError as e:
        print(f"  Error parsing IMF response: {e}")
    
    return None


# ============================================================
# MAIN FUNCTIONS
# ============================================================

def build_forecast_entry(country_code: str, api_data: Optional[Dict] = None) -> Dict:
    """
    Build a forecast entry for a country.
    Uses API data if available, falls back to manual entry.
    """
    metadata = COUNTRY_METADATA.get(country_code, {})
    manual = MANUAL_FORECASTS.get(country_code, {})
    
    entry = {
        "country_name": metadata.get("country_name", country_code),
        "flag": metadata.get("flag", ""),
        "central_bank": metadata.get("central_bank", ""),
        "source": manual.get("source", ""),
        "source_full": manual.get("source_full", ""),
        "source_url": manual.get("source_url", ""),
        "publication_date": manual.get("publication_date", ""),
        "forecast_type": manual.get("forecast_type", ""),
        "measure": manual.get("measure", ""),
        "projections": manual.get("projections", {}),
        "key_quote": manual.get("key_quote", ""),
        "note": manual.get("note", ""),
        "policy_rate": manual.get("policy_rate", {})
    }
    
    # If we have API data, update projections
    if api_data:
        # Merge API data with manual (API takes precedence for matching years)
        merged = dict(entry["projections"])
        for year, value in api_data.items():
            merged[str(year)] = value
        entry["projections"] = merged
        entry["note"] = entry["note"] + " (API-updated)"
    
    return entry


def fetch_all_forecasts(use_api: bool = True) -> Dict:
    """
    Fetch forecasts for all countries.
    """
    forecasts = {}
    
    for country_code in DISPLAY_ORDER:
        print(f"\nProcessing {country_code}...")
        
        api_data = None
        
        if use_api:
            # Try to fetch from API based on country
            if country_code == "US":
                api_data = fetch_fomc_sep()
            elif country_code == "EA":
                api_data = fetch_ecb_mpd()
            elif country_code == "CN":
                api_data = fetch_imf_weo("CHN")
            # Other countries don't have reliable APIs - use manual data
        
        forecasts[country_code] = build_forecast_entry(country_code, api_data)
    
    return forecasts


def update_manual_entry(country_code: str) -> None:
    """
    Interactive mode to update manual forecast entry.
    """
    print(f"\n{'='*60}")
    print(f"Updating {country_code} - {COUNTRY_METADATA[country_code]['country_name']}")
    print(f"{'='*60}")
    
    current = MANUAL_FORECASTS.get(country_code, {})
    print(f"\nCurrent projections: {current.get('projections', {})}")
    print(f"Last updated: {current.get('last_updated', 'Unknown')}")
    
    print("\nEnter new values (press Enter to keep current):")
    
    # Get new projections
    new_projections = {}
    for year in ["2025", "2026", "2027", "2028"]:
        current_val = current.get("projections", {}).get(year)
        prompt = f"  {year} [{current_val if current_val else 'N/A'}]: "
        new_val = input(prompt).strip()
        if new_val:
            try:
                new_projections[year] = float(new_val)
            except ValueError:
                print(f"    Invalid value, keeping current")
                if current_val:
                    new_projections[year] = current_val
        elif current_val:
            new_projections[year] = current_val
    
    # Get key quote
    current_quote = current.get("key_quote", "")
    new_quote = input(f"\n  Key quote [{current_quote[:50]}...]: ").strip()
    
    # Get policy rate
    current_rate = current.get("policy_rate", {}).get("rate", "")
    new_rate = input(f"  Policy rate [{current_rate}]: ").strip()
    
    print(f"\nNew projections: {new_projections}")
    confirm = input("Save these changes? [y/N]: ").strip().lower()
    
    if confirm == 'y':
        # Update the MANUAL_FORECASTS dict
        # Note: This only updates in memory - you'd need to edit the file to persist
        MANUAL_FORECASTS[country_code]["projections"] = new_projections
        MANUAL_FORECASTS[country_code]["last_updated"] = date.today().isoformat()
        if new_quote:
            MANUAL_FORECASTS[country_code]["key_quote"] = new_quote
        if new_rate:
            MANUAL_FORECASTS[country_code]["policy_rate"]["rate"] = new_rate
        print("  Updated! (Note: Edit the script to persist changes)")
    else:
        print("  Cancelled")


def save_forecasts(forecasts: Dict, output_file: str) -> None:
    """
    Save forecasts to JSON file.
    """
    output = {
        "metadata": {
            "last_updated": date.today().isoformat(),
            "description": "Central bank inflation forecasts - single source of truth for dashboard",
            "generated_by": "fetch_cb_forecasts.py"
        },
        "forecasts": forecasts,
        "display_order": DISPLAY_ORDER
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch central bank inflation forecasts"
    )
    parser.add_argument(
        "--update-manual",
        action="store_true",
        help="Interactive mode to update manual forecast entries"
    )
    parser.add_argument(
        "--force",
        action="store_true", 
        help="Force refresh all data from APIs"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Skip API calls, use only manual data"
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help=f"Output file path (default: {OUTPUT_FILE})"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Central Bank Forecasts Fetcher")
    print("="*60)
    
    if args.update_manual:
        # Interactive mode
        print("\nInteractive update mode")
        print("Select country to update:")
        for i, code in enumerate(DISPLAY_ORDER):
            name = COUNTRY_METADATA[code]["country_name"]
            print(f"  {i+1}. {code} - {name}")
        print("  0. All countries")
        print("  q. Quit")
        
        choice = input("\nChoice: ").strip().lower()
        
        if choice == 'q':
            return
        elif choice == '0':
            for code in DISPLAY_ORDER:
                update_manual_entry(code)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(DISPLAY_ORDER):
                    update_manual_entry(DISPLAY_ORDER[idx])
            except ValueError:
                print("Invalid choice")
                return
    
    # Fetch all forecasts
    print("\nFetching forecasts...")
    use_api = not args.no_api
    forecasts = fetch_all_forecasts(use_api=use_api)
    
    # Save to file
    save_forecasts(forecasts, args.output)
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    for code in DISPLAY_ORDER:
        fc = forecasts.get(code, {})
        proj = fc.get("projections", {})
        y2026 = proj.get("2026", "N/A")
        print(f"  {code}: 2026 forecast = {y2026}%")


if __name__ == "__main__":
    main()
