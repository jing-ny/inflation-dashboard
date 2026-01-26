# -*- coding: utf-8 -*-
"""
Fetch 10-Year Historical CPI Data for Inflation Dashboard
=========================================================

This script fetches real historical CPI data from official APIs and outputs
JSON files that can be embedded in the dashboard HTML pages.

Countries covered:
- 🇺🇸 United States (BLS API)
- 🇬🇧 United Kingdom (FRED API)
- 🇩🇪 Germany (FRED API)
- 🇪🇺 Euro Area (ECB API)
- 🇦🇺 Australia (FRED API - quarterly)
- 🇳🇿 New Zealand (FRED API - quarterly)
- 🇿🇦 South Africa (FRED API)
- 🇨🇳 China (FRED API)
- 🇯🇵 Japan (FRED API)

Usage:
    python fetch_historical_cpi.py

Output:
    - data/historical_cpi.json (all countries combined)
    - data/us_cpi.json, data/uk_cpi.json, etc. (individual files)

Requirements:
    pip install requests python-dotenv

Environment:
    FRED_API_KEY - Get free at https://fred.stlouisfed.org/docs/api/api_key.html
    BLS_API_KEY  - Optional, get at https://www.bls.gov/developers/
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

FRED_API_KEY = os.environ.get("FRED_API_KEY")
BLS_API_KEY = os.environ.get("BLS_API_KEY")

# Output directory
OUTPUT_DIR = "data"

# -----------------------------------------------------------------------------
# Country Configuration
# -----------------------------------------------------------------------------

COUNTRIES = {
    "US": {
        "name": "United States",
        "flag": "🇺🇸",
        "api": "FRED",
        "series_id": "CPIAUCNS",  # CPI-U All Urban Consumers, Not Seasonally Adjusted (direct from BLS via FRED)
        "frequency": "monthly",
        "target": 2.0,
        "source": "Bureau of Labor Statistics via FRED"
    },
    "CA": {
        "name": "Canada",
        "flag": "🇨🇦",
        "api": "FRED",
        "series_id": "CANCPIALLMINMEI",
        "frequency": "monthly",
        "target": 2.0,  # midpoint of 1-3%
        "source": "Statistics Canada via OECD/FRED"
    },
    "UK": {
        "name": "United Kingdom",
        "flag": "🇬🇧",
        "api": "FRED",
        "series_id": "GBRCPIALLMINMEI",
        "frequency": "monthly",
        "target": 2.0,
        "source": "ONS via OECD/FRED"
    },
    "EA": {
        "name": "Euro Area",
        "flag": "🇪🇺",
        "api": "ECB",
        "series_id": "ICP.M.U2.N.000000.4.ANR",
        "frequency": "monthly",
        "target": 2.0,
        "source": "Eurostat via ECB"
    },
    "AU": {
        "name": "Australia",
        "flag": "🇦🇺",
        "api": "ABS",
        "series_id": "CPI",  # ABS CPI dataflow
        "frequency": "monthly",  # Now monthly since Nov 2025
        "target": 2.5,  # midpoint of 2-3%
        "source": "Australian Bureau of Statistics"
    },
    "NZ": {
        "name": "New Zealand",
        "flag": "🇳🇿",
        "api": "FRED",
        "series_id": "NZLCPIALLQINMEI",
        "frequency": "quarterly",
        "target": 2.0,  # midpoint of 1-3%
        "source": "Stats NZ via OECD/FRED"
    },
    "ZA": {
        "name": "South Africa",
        "flag": "🇿🇦",
        "api": "FRED",
        "series_id": "ZAFCPIALLMINMEI",
        "frequency": "monthly",
        "target": 4.5,  # midpoint of 3-6%
        "source": "Stats SA via OECD/FRED"
    },
    "CN": {
        "name": "China",
        "flag": "🇨🇳",
        "api": "FRED",
        "series_id": "CHNCPIALLMINMEI",
        "frequency": "monthly",
        "target": 3.0,
        "source": "NBS via OECD/FRED"
    }
    # Note: Japan temporarily removed - FRED's COICOP 1999 series discontinued June 2021,
    # COICOP 2018 series not yet available via FRED. Will re-add when data source resolved.
}


# -----------------------------------------------------------------------------
# API Fetchers
# -----------------------------------------------------------------------------

def fetch_fred_series(series_id: str, start_date: str = "2015-01-01") -> List[Dict]:
    """
    Fetch CPI index series from FRED API.
    
    Args:
        series_id: FRED series identifier
        start_date: Start date in YYYY-MM-DD format
        
    Returns:
        List of {"date": "YYYY-MM-DD", "value": float} observations
    """
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not set. Get one free at fred.stlouisfed.org")
    
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "asc"
    }
    
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    observations = []
    for obs in data.get("observations", []):
        if obs["value"] != ".":  # FRED uses "." for missing
            observations.append({
                "date": obs["date"],
                "value": float(obs["value"])
            })
    
    return observations


def fetch_bls_series(series_id: str, start_year: int = 2015) -> List[Dict]:
    """
    Fetch CPI index series from BLS API.
    
    Args:
        series_id: BLS series identifier
        start_year: Starting year
        
    Returns:
        List of {"date": "YYYY-MM-DD", "value": float} observations
    """
    end_year = datetime.now().year
    
    # BLS API limits to 20 years per request
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    
    headers = {"Content-type": "application/json"}
    payload = {
        "seriesid": [series_id],
        "startyear": str(start_year),
        "endyear": str(end_year)
    }
    
    # Add API key if available (higher rate limits)
    if BLS_API_KEY:
        payload["registrationkey"] = BLS_API_KEY
    
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(f"BLS API error: {data.get('message', 'Unknown error')}")
    
    observations = []
    for series in data.get("Results", {}).get("series", []):
        for item in series.get("data", []):
            year = item["year"]
            month = item["period"].replace("M", "")
            if month.isdigit():  # Skip annual averages (M13)
                date_str = f"{year}-{month.zfill(2)}-01"
                observations.append({
                    "date": date_str,
                    "value": float(item["value"])
                })
    
    # BLS returns newest first, reverse to chronological
    observations.sort(key=lambda x: x["date"])
    return observations


def fetch_ecb_series(series_id: str, start_date: str = "2015-01-01") -> List[Dict]:
    """
    Fetch HICP series from ECB SDMX API.
    
    Note: ECB series ICP.M.U2.N.000000.4.ANR already provides YoY inflation rate,
    not the index. This is the annual rate of change.
    
    Args:
        series_id: ECB series identifier (e.g., "ICP.M.U2.N.000000.4.ANR")
        start_date: Start date in YYYY-MM-DD format
        
    Returns:
        List of {"date": "YYYY-MM-DD", "value": float} observations
    """
    # ECB SDMX endpoint
    # The series ICP.M.U2.N.000000.4.ANR gives annual rate of change directly
    base_url = "https://data-api.ecb.europa.eu/service/data"
    
    # Parse series key: ICP.M.U2.N.000000.4.ANR
    # Format: dataflow/key
    parts = series_id.split(".")
    dataflow = parts[0]  # ICP
    key = ".".join(parts[1:])  # M.U2.N.000000.4.ANR
    
    url = f"{base_url}/{dataflow}/{key}"
    params = {
        "format": "csvdata",
        "startPeriod": start_date[:7],  # YYYY-MM
        "detail": "dataonly"
    }
    
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    
    # Parse CSV response
    observations = []
    lines = resp.text.strip().split("\n")
    
    if len(lines) > 1:
        # Find column indices from header
        header = lines[0].split(",")
        try:
            date_idx = header.index("TIME_PERIOD")
            value_idx = header.index("OBS_VALUE")
        except ValueError:
            # Try alternate column names
            date_idx = next(i for i, h in enumerate(header) if "TIME" in h or "PERIOD" in h)
            value_idx = next(i for i, h in enumerate(header) if "OBS" in h or "VALUE" in h)
        
        for line in lines[1:]:
            cols = line.split(",")
            if len(cols) > max(date_idx, value_idx):
                date_str = cols[date_idx].strip('"')
                value_str = cols[value_idx].strip('"')
                if value_str and value_str != "":
                    # ECB dates are YYYY-MM, convert to YYYY-MM-01
                    if len(date_str) == 7:
                        date_str = f"{date_str}-01"
                    observations.append({
                        "date": date_str,
                        "value": float(value_str)
                    })
    
    observations.sort(key=lambda x: x["date"])
    return observations


def fetch_abs_cpi(start_date: str = "2015-01-01") -> List[Dict]:
    """
    Fetch CPI YoY inflation rate for Australia.
    
    The ABS restructured their API in November 2025 with new dataflows.
    This function uses FRED OECD data as the reliable source.
    
    Note: FRED OECD quarterly data has ~1-2 quarter lag, but is stable.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        
    Returns:
        List of {"date": "YYYY-MM-DD", "value": float} YoY inflation rates
    """
    # Use FRED OECD series - reliable but quarterly with some lag
    # AUSCPIALLQINMEI = Australia CPI All Items (Quarterly, Index)
    print(f"  Using FRED OECD quarterly series for Australia...")
    
    try:
        raw_data = fetch_fred_series("AUSCPIALLQINMEI", start_date)
        observations = calculate_yoy_from_index(raw_data, "quarterly")
        return observations
    except Exception as e:
        print(f"  Warning: FRED fetch failed: {e}")
        return []


def fetch_oecd_series(series_id: str, start_date: str = "2015-01-01") -> List[Dict]:
    """
    Fetch CPI series from OECD Data Explorer API.
    
    This is used for Japan since FRED's COICOP 1999 series was discontinued in 2021.
    OECD provides COICOP 2018 data with current observations.
    
    Args:
        series_id: OECD series filter (e.g., "JPN.CPI._T.GY.M")
                   Format: REF_AREA.MEASURE.EXPENDITURE.TRANSFORMATION.FREQ
        start_date: Start date in YYYY-MM-DD format
        
    Returns:
        List of {"date": "YYYY-MM-DD", "value": float} observations
    """
    # OECD Data Explorer SDMX API for Consumer Prices
    # Dataset: PRICES_CPI (Consumer Price Indices)
    base_url = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0"
    
    # Parse series filter
    # JPN.CPI._T.GY.M means:
    # REF_AREA=JPN, MEASURE=CPI, EXPENDITURE=_T (Total), TRANSFORMATION=GY (YoY growth), FREQ=M (Monthly)
    url = f"{base_url}/{series_id}"
    params = {
        "format": "csv",
        "startPeriod": start_date[:7],  # YYYY-MM
    }
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # If main OECD API fails, try the simpler SDMX endpoint
        # Alternative: use OECD stat data API
        alt_url = "https://stats.oecd.org/SDMX-JSON/data/PRICES_CPI"
        parts = series_id.split(".")
        country = parts[0]  # JPN
        
        # Try OECD.Stat API format
        filter_str = f"{country}.CPALTT01.GY.M"  # All items, YoY growth, Monthly
        alt_full_url = f"{alt_url}/{filter_str}/all"
        
        try:
            resp = requests.get(alt_full_url, params={"startTime": start_date[:4]}, timeout=30)
            resp.raise_for_status()
            # Parse SDMX-JSON format
            return parse_oecd_json(resp.json(), start_date)
        except Exception:
            raise ValueError(f"OECD API failed for {series_id}: {e}")
    
    # Parse CSV response
    observations = []
    lines = resp.text.strip().split("\n")
    
    if len(lines) > 1:
        header = lines[0].split(",")
        try:
            date_idx = header.index("TIME_PERIOD")
            value_idx = header.index("OBS_VALUE")
        except ValueError:
            # Try finding columns with similar names
            date_idx = next((i for i, h in enumerate(header) if "TIME" in h.upper() or "PERIOD" in h.upper()), None)
            value_idx = next((i for i, h in enumerate(header) if "OBS" in h.upper() or "VALUE" in h.upper()), None)
            if date_idx is None or value_idx is None:
                raise ValueError(f"Cannot parse OECD response headers: {header}")
        
        for line in lines[1:]:
            cols = line.split(",")
            if len(cols) > max(date_idx, value_idx):
                date_str = cols[date_idx].strip('"')
                value_str = cols[value_idx].strip('"')
                if value_str and value_str not in ("", "NaN"):
                    # OECD dates are YYYY-MM for monthly data
                    if len(date_str) == 7:
                        date_str = f"{date_str}-01"
                    observations.append({
                        "date": date_str,
                        "value": float(value_str)
                    })
    
    observations.sort(key=lambda x: x["date"])
    return observations


def parse_oecd_json(data: dict, start_date: str) -> List[Dict]:
    """Parse OECD SDMX-JSON format response."""
    observations = []
    
    try:
        # Navigate SDMX-JSON structure
        datasets = data.get("dataSets", [{}])[0]
        series_data = datasets.get("series", {})
        
        # Get time periods from structure
        structure = data.get("structure", {})
        dimensions = structure.get("dimensions", {})
        observation_dims = dimensions.get("observation", [])
        
        time_periods = []
        for dim in observation_dims:
            if dim.get("id") == "TIME_PERIOD":
                time_periods = [v.get("id") for v in dim.get("values", [])]
                break
        
        # Extract values from first series
        for series_key, series_vals in series_data.items():
            obs_dict = series_vals.get("observations", {})
            for idx_str, val_list in obs_dict.items():
                idx = int(idx_str)
                if idx < len(time_periods):
                    date_str = time_periods[idx]
                    value = val_list[0] if val_list else None
                    if value is not None and date_str >= start_date[:7]:
                        if len(date_str) == 7:
                            date_str = f"{date_str}-01"
                        observations.append({
                            "date": date_str,
                            "value": float(value)
                        })
            break  # Only need first series
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Failed to parse OECD JSON response: {e}")
    
    observations.sort(key=lambda x: x["date"])
    return observations


# -----------------------------------------------------------------------------
# YoY Calculation
# -----------------------------------------------------------------------------

def calculate_yoy_from_index(observations: List[Dict], frequency: str = "monthly") -> List[Dict]:
    """
    Calculate Year-over-Year inflation rate from CPI index values.
    
    Args:
        observations: List of {"date": "YYYY-MM-DD", "value": float} (CPI index)
        frequency: "monthly" or "quarterly"
        
    Returns:
        List of {"date": "YYYY-MM", "value": float} (YoY inflation rate)
    """
    # Create lookup by date
    by_date = {obs["date"]: obs["value"] for obs in observations}
    
    yoy_data = []
    
    for obs in observations:
        current_date = datetime.strptime(obs["date"], "%Y-%m-%d")
        
        # Find same period one year ago
        if frequency == "quarterly":
            # Go back 4 quarters (12 months)
            year_ago = current_date - timedelta(days=365)
            # Snap to first of quarter
            year_ago = year_ago.replace(day=1)
        else:
            # Monthly: go back 12 months
            year_ago = current_date.replace(year=current_date.year - 1)
        
        year_ago_str = year_ago.strftime("%Y-%m-%d")
        
        if year_ago_str in by_date:
            current_value = obs["value"]
            year_ago_value = by_date[year_ago_str]
            
            yoy = ((current_value / year_ago_value) - 1) * 100
            
            yoy_data.append({
                "date": obs["date"][:7],  # YYYY-MM format
                "value": round(yoy, 2)
            })
    
    return yoy_data


# -----------------------------------------------------------------------------
# Main Fetch Functions
# -----------------------------------------------------------------------------

def fetch_country_data(country_code: str) -> Dict:
    """
    Fetch historical CPI data for a single country.
    
    Returns:
        {
            "code": "US",
            "name": "United States",
            "flag": "🇺🇸",
            "target": 2.0,
            "frequency": "monthly",
            "source": "...",
            "last_updated": "2025-01-25",
            "history": [{"date": "2015-01", "value": 0.1}, ...]
        }
    """
    config = COUNTRIES[country_code]
    print(f"  Fetching {config['flag']} {config['name']}...")
    
    try:
        if config["api"] == "FRED":
            raw_data = fetch_fred_series(config["series_id"])
            # Check if this series is already YoY data (not an index)
            if config.get("data_type") == "yoy":
                # Data is already YoY percent change, just format it
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)} 
                           for obs in raw_data]
            else:
                # Data is an index, calculate YoY
                yoy_data = calculate_yoy_from_index(raw_data, config["frequency"])
            
        elif config["api"] == "BLS":
            raw_data = fetch_bls_series(config["series_id"])
            yoy_data = calculate_yoy_from_index(raw_data, config["frequency"])
            
        elif config["api"] == "ECB":
            # ECB series already provides YoY rate
            raw_data = fetch_ecb_series(config["series_id"])
            yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)} 
                       for obs in raw_data]
            
        elif config["api"] == "OECD":
            # OECD Data Explorer API - used for Japan (COICOP 2018)
            raw_data = fetch_oecd_series(config["series_id"])
            # OECD series provides YoY rate directly
            yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)} 
                       for obs in raw_data]
                       
        elif config["api"] == "ABS":
            # Australian Bureau of Statistics Data API
            raw_data = fetch_abs_cpi()
            # ABS data is already YoY percentage change
            yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)} 
                       for obs in raw_data]
        else:
            raise ValueError(f"Unknown API: {config['api']}")
        
        # Get latest data point
        if yoy_data:
            latest = yoy_data[-1]
            previous = yoy_data[-2] if len(yoy_data) > 1 else None
        else:
            latest = None
            previous = None
        
        return {
            "code": country_code,
            "name": config["name"],
            "flag": config["flag"],
            "target": config["target"],
            "frequency": config["frequency"],
            "source": config["source"],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "latest": latest,
            "previous": previous,
            "history": yoy_data
        }
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return {
            "code": country_code,
            "name": config["name"],
            "flag": config["flag"],
            "target": config["target"],
            "frequency": config["frequency"],
            "source": config["source"],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "error": str(e),
            "history": []
        }


def fetch_all_countries() -> Dict[str, Dict]:
    """
    Fetch historical CPI data for all countries.
    
    Returns:
        Dictionary keyed by country code
    """
    print("Fetching 10-year historical CPI data...")
    print("=" * 50)
    
    all_data = {}
    
    for code in COUNTRIES:
        data = fetch_country_data(code)
        all_data[code] = data
        
        if "error" not in data and data.get("latest"):
            print(f"    ✅ {len(data['history'])} data points, latest: {data['latest']['date']} = {data['latest']['value']}%")
        elif "error" in data:
            print(f"    ❌ Failed: {data['error']}")
        else:
            print(f"    ⚠️ No data available")
    
    print("=" * 50)
    print("Done!")
    
    return all_data


# -----------------------------------------------------------------------------
# Output Functions
# -----------------------------------------------------------------------------

def save_json(data: any, filename: str):
    """Save data to JSON file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved: {filepath}")


def generate_js_data(all_data: Dict[str, Dict]) -> str:
    """
    Generate JavaScript code that can be directly embedded in HTML.
    
    Returns a string like:
    const INFLATION_DATA = { ... };
    """
    js_code = "// Auto-generated by fetch_historical_cpi.py\n"
    js_code += f"// Generated: {datetime.now().isoformat()}\n\n"
    js_code += "const INFLATION_DATA = "
    js_code += json.dumps(all_data, indent=2, ensure_ascii=False)
    js_code += ";\n"
    
    return js_code


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Check for API key
    if not FRED_API_KEY:
        print("⚠️  Warning: FRED_API_KEY not set.")
        print("   Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   Add to .env.local: FRED_API_KEY=your_key_here")
        print()
    
    # Fetch all data
    all_data = fetch_all_countries()
    
    # Save combined JSON
    save_json(all_data, "historical_cpi.json")
    
    # Save individual country files
    for code, data in all_data.items():
        save_json(data, f"{code.lower()}_cpi.json")
    
    # Save JavaScript version for direct HTML embedding
    js_code = generate_js_data(all_data)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "inflation_data.js"), "w", encoding="utf-8") as f:
        f.write(js_code)
    print(f"Saved: {OUTPUT_DIR}/inflation_data.js")
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    for code, data in all_data.items():
        if "error" not in data and data.get("latest"):
            latest = data["latest"]
            target = data["target"]
            diff = latest["value"] - target
            status = "🔴" if diff > 1 else ("🟢" if diff < -0.5 else "🟡")
            print(f"{data['flag']} {code}: {latest['value']:5.1f}% (target: {target}%) {status}")
        else:
            print(f"{data.get('flag', '❓')} {code}: No data")
