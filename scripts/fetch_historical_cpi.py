# -*- coding: utf-8 -*-
"""
Fetch Historical CPI Data for Inflation Dashboard
==================================================

This script fetches CPI inflation data from official APIs (primarily FRED)
and MERGES it with existing data in docs/data/historical_cpi.json.

Key Features:
- Fetches from FRED API for most countries
- Uses ECB API for Euro Area (more current than FRED)
- MERGES with existing data - does NOT overwrite manually verified values
- Only updates if FRED has newer data than what's already stored
- Supports all 15 dashboard countries

Countries covered:
- 🇺🇸 United States (FRED - BLS)
- 🇪🇺 Euro Area (ECB API)
- 🇬🇧 United Kingdom (FRED - OECD)
- 🇨🇦 Canada (FRED - OECD)
- 🇦🇺 Australia (FRED - OECD)
- 🇳🇿 New Zealand (FRED - OECD)
- 🇿🇦 South Africa (FRED - OECD)
- 🇯🇵 Japan (FRED - OECD)
- 🇨🇳 China (FRED - OECD)
- 🇮🇳 India (FRED - OECD)
- 🇰🇷 South Korea (FRED - OECD)
- 🇸🇬 Singapore (FRED - OECD)
- 🇧🇷 Brazil (FRED - OECD)
- 🇲🇽 Mexico (FRED - OECD)
- 🇻🇪 Venezuela (FRED - World Bank)

Usage:
    python fetch_historical_cpi.py              # Merge mode (default)
    python fetch_historical_cpi.py --overwrite  # Full overwrite (use with caution)
    python fetch_historical_cpi.py --dry-run    # Preview without saving
    python fetch_historical_cpi.py --country US # Fetch single country

Output:
    - docs/data/historical_cpi.json (merged/updated)

Requirements:
    pip install requests python-dotenv

Environment:
    FRED_API_KEY - Get free at https://fred.stlouisfed.org/docs/api/api_key.html
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    load_dotenv('.env')
except ImportError:
    pass

FRED_API_KEY = os.environ.get("FRED_API_KEY")

# Output directory - single source of truth
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "data" if Path(__file__).parent.name == "scripts" else Path("docs/data")
DATA_FILE = OUTPUT_DIR / "historical_cpi.json"

# -----------------------------------------------------------------------------
# Country Configuration - All 15 Countries
# -----------------------------------------------------------------------------

COUNTRIES = {
    "US": {
        "name": "United States",
        "flag": "🇺🇸",
        "target": 2.0,
        "source": "BLS",
        "source_url": "https://www.bls.gov/cpi/",
        "api": "BLS",
        "series_id": "CUUR0000SA0",  # CPI-U All Urban Consumers, NSA (index) — same series as FRED CPIAUCNS
        "fred_series": "CPIAUCNS",  # FRED fallback if BLS API fails
        "frequency": "monthly",
        "data_type": "index",  # Need to calculate YoY
    },
    "EA": {
        "name": "Euro Area",
        "flag": "🇪🇺",
        "target": 2.0,
        "source": "Eurostat",
        "source_url": "https://ec.europa.eu/eurostat/",
        "api": "ECB",
        "series_id": "ICP.M.U2.N.000000.4.ANR",  # Already YoY rate
        "frequency": "monthly",
        "data_type": "yoy",
    },
    "UK": {
        "name": "United Kingdom",
        "flag": "🇬🇧",
        "target": 2.0,
        "source": "ONS",
        "source_url": "https://www.ons.gov.uk/economy/inflationandpriceindices",
        "fred_series": "GBRCPIALLMINMEI",  # OECD index
        "frequency": "monthly",
        "data_type": "index",
        "lag_months": 2,  # FRED typically lags ONS by 1-2 months
    },
    "CA": {
        "name": "Canada",
        "flag": "🇨🇦",
        "target": 2.0,
        "source": "Statistics Canada",
        "source_url": "https://www.statcan.gc.ca/",
        "fred_series": "CANCPIALLMINMEI",  # OECD index
        "frequency": "monthly",
        "data_type": "index",
        "lag_months": 2,
    },
    "AU": {
        "name": "Australia",
        "flag": "🇦🇺",
        "target": 2.5,
        "source": "ABS",
        "source_url": "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/",
        "fred_series": "AUSCPIALLQINMEI",  # OECD quarterly index
        "frequency": "quarterly",  # Note: ABS now publishes monthly, but FRED is quarterly
        "data_type": "index",
        "lag_months": 3,
        "notes": "ABS transitioned to monthly CPI in late 2025. FRED still quarterly.",
    },
    "NZ": {
        "name": "New Zealand",
        "flag": "🇳🇿",
        "target": 2.0,
        "source": "Stats NZ",
        "source_url": "https://www.stats.govt.nz/indicators/consumers-price-index-cpi/",
        "fred_series": "NZLCPIALLQINMEI",  # OECD quarterly index
        "frequency": "quarterly",
        "data_type": "index",
    },
    "ZA": {
        "name": "South Africa",
        "flag": "🇿🇦",
        "target": 3.0,  # Changed from 4.5% (3-6% range) to 3% in Nov 2025
        "source": "Stats SA",
        "source_url": "https://www.statssa.gov.za/",
        "fred_series": "ZAFCPIALLMINMEI",  # OECD index
        "frequency": "monthly",
        "data_type": "index",
        "lag_months": 6,  # FRED significantly lags Stats SA
        "notes": "SARB target changed to 3% in 2025",
    },
    "JP": {
        "name": "Japan",
        "flag": "🇯🇵",
        "target": 2.0,
        "source": "MIC",
        "source_url": "https://www.stat.go.jp/english/data/cpi/",
        "fred_series": "JPNCPALTT01IXNBM",  # COICOP 2018 index, monthly
        "fred_series_alt": "JPNCPIALLMINMEI",  # COICOP 1999 fallback (discontinued Jun 2021 but may still serve data)
        "frequency": "monthly",
        "data_type": "index",
        "notes": "Primary: COICOP 2018 index. Fallback: COICOP 1999 (discontinued Jun 2021). Manual supplement recommended for latest data.",
    },
    "CN": {
        "name": "China",
        "flag": "🇨🇳",
        "target": 3.0,
        "source": "NBS",
        "source_url": "https://www.stats.gov.cn/english/",
        "fred_series": "CHNCPIALLMINMEI",  # OECD index
        "frequency": "monthly",
        "data_type": "index",
    },
    "IN": {
        "name": "India",
        "flag": "🇮🇳",
        "target": 4.0,
        "source": "MOSPI",
        "source_url": "https://www.mospi.gov.in/",
        "fred_series": "INDCPIALLMINMEI",  # OECD index
        "frequency": "monthly",
        "data_type": "index",
    },
    "KR": {
        "name": "South Korea",
        "flag": "🇰🇷",
        "target": 2.0,
        "source": "KOSTAT",
        "source_url": "https://kostat.go.kr/",
        "fred_series": "KORCPALTT01IXNBM",  # COICOP 2018 index, monthly
        "fred_series_alt": "KORCPIALLMINMEI",  # COICOP 1999 fallback (discontinued Nov 2023)
        "frequency": "monthly",
        "data_type": "index",
        "notes": "Primary: COICOP 2018 index. Fallback: COICOP 1999 (discontinued Nov 2023). Manual supplement recommended for latest data.",
    },
    "SG": {
        "name": "Singapore",
        "flag": "🇸🇬",
        "target": 2.0,
        "source": "SingStat",
        "source_url": "https://www.singstat.gov.sg/",
        "fred_series": "FPCPITOTLZGSGP",  # World Bank annual (OECD series broken)
        "frequency": "annual",
        "data_type": "yoy",  # Already YoY
        "notes": "FRED OECD series SGPCPIALLMINMEI returns 400 error. Using World Bank annual data. Manual supplement recommended.",
    },
    "BR": {
        "name": "Brazil",
        "flag": "🇧🇷",
        "target": 3.0,
        "source": "IBGE",
        "source_url": "https://www.ibge.gov.br/en/statistics/economic/prices-and-costs.html",
        "fred_series": "BRACPIALLMINMEI",
        "frequency": "monthly",
        "data_type": "index",
        "notes": "BCB target 3% with 1.5pp tolerance band (1.5-4.5%)",
    },
    "MX": {
        "name": "Mexico",
        "flag": "🇲🇽",
        "target": 3.0,
        "source": "INEGI",
        "source_url": "https://www.inegi.org.mx/temas/inpc/",
        "fred_series": "MEXCPIALLMINMEI",
        "frequency": "monthly",
        "data_type": "index",
        "notes": "Banxico target 3% with ±1pp tolerance band (2-4%)",
    },
    "VE": {
        "name": "Venezuela",
        "flag": "🇻🇪",
        "target": None,  # No formal target
        "source": "BCV",
        "source_url": "https://www.bcv.org.ve/",
        "fred_series": "FPCPITOTLZGVEN",  # World Bank, annual
        "frequency": "annual",
        "data_type": "yoy",  # Already YoY
        "notes": "Post-hyperinflation period only. Data updates irregularly.",
    },
}

# Display order for output
DISPLAY_ORDER = ['US', 'EA', 'UK', 'CA', 'AU', 'NZ', 'ZA', 'BR', 'MX', 'JP', 'CN', 'IN', 'KR', 'SG', 'VE']


# -----------------------------------------------------------------------------
# API Fetchers
# -----------------------------------------------------------------------------

def fetch_fred_series(series_id: str, start_date: str = "2015-01-01") -> List[Dict]:
    """
    Fetch series from FRED API.
    
    Returns:
        List of {"date": "YYYY-MM-DD", "value": float} observations
    """
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not set")
    
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
    """Fetch a CPI index series from the BLS Public Data API.

    Without a key the API serves up to 10 years; with BLS_API_KEY set in env,
    we POST and request the full window since `start_year`.

    Returns observations as a list of {"date": "YYYY-MM-DD", "value": float}
    sorted ascending. Missing months (BLS uses "-") are skipped.
    """
    api_key = os.environ.get("BLS_API_KEY")
    end_year = datetime.now().year

    if api_key:
        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        payload = {
            "seriesid": [series_id],
            "startyear": str(start_year),
            "endyear": str(end_year),
            "registrationkey": api_key,
        }
        resp = requests.post(url, json=payload, timeout=30)
    else:
        # Unkeyed GET — returns last ~10 years for the series
        url = f"https://api.bls.gov/publicAPI/v2/timeseries/data/{series_id}"
        resp = requests.get(url, timeout=30)

    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "REQUEST_SUCCEEDED":
        msg = data.get("message", ["unknown"])
        raise RuntimeError(f"BLS API error: {msg}")

    series_list = data.get("Results", {}).get("series", [])
    if not series_list:
        return []

    observations = []
    for obs in series_list[0].get("data", []):
        if obs.get("value") in (None, "", "-"):
            continue
        period = obs.get("period", "")
        # BLS monthly periods are M01..M12; M13 is annual average — skip annual.
        if not period.startswith("M") or period == "M13":
            continue
        try:
            month = int(period[1:])
        except ValueError:
            continue
        date_str = f"{obs['year']}-{month:02d}-01"
        observations.append({"date": date_str, "value": float(obs["value"])})

    observations.sort(key=lambda x: x["date"])
    return observations


def fetch_ecb_series(series_id: str, start_date: str = "2015-01-01") -> List[Dict]:
    """
    Fetch HICP YoY rate from ECB SDMX API.
    
    The ECB series ICP.M.U2.N.000000.4.ANR already provides YoY inflation rate.
    """
    base_url = "https://data-api.ecb.europa.eu/service/data"
    
    parts = series_id.split(".")
    dataflow = parts[0]  # ICP
    key = ".".join(parts[1:])  # M.U2.N.000000.4.ANR
    
    url = f"{base_url}/{dataflow}/{key}"
    params = {
        "format": "csvdata",
        "startPeriod": start_date[:7],
        "detail": "dataonly"
    }
    
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    
    observations = []
    lines = resp.text.strip().split("\n")
    
    if len(lines) > 1:
        header = lines[0].split(",")
        try:
            date_idx = header.index("TIME_PERIOD")
            value_idx = header.index("OBS_VALUE")
        except ValueError:
            date_idx = next(i for i, h in enumerate(header) if "TIME" in h or "PERIOD" in h)
            value_idx = next(i for i, h in enumerate(header) if "OBS" in h or "VALUE" in h)
        
        for line in lines[1:]:
            cols = line.split(",")
            if len(cols) > max(date_idx, value_idx):
                date_str = cols[date_idx].strip('"')
                value_str = cols[value_idx].strip('"')
                if value_str:
                    if len(date_str) == 7:
                        date_str = f"{date_str}-01"
                    observations.append({
                        "date": date_str,
                        "value": float(value_str)
                    })
    
    observations.sort(key=lambda x: x["date"])
    return observations


# -----------------------------------------------------------------------------
# YoY Calculation
# -----------------------------------------------------------------------------

def calculate_yoy_from_index(observations: List[Dict], frequency: str = "monthly") -> List[Dict]:
    """
    Calculate Year-over-Year inflation rate from CPI index values.
    """
    by_date = {obs["date"]: obs["value"] for obs in observations}
    yoy_data = []
    
    for obs in observations:
        current_date = datetime.strptime(obs["date"], "%Y-%m-%d")
        
        if frequency == "quarterly":
            year_ago = current_date - timedelta(days=365)
            year_ago = year_ago.replace(day=1)
        else:
            year_ago = current_date.replace(year=current_date.year - 1)
        
        year_ago_str = year_ago.strftime("%Y-%m-%d")
        
        if year_ago_str in by_date:
            current_value = obs["value"]
            year_ago_value = by_date[year_ago_str]
            yoy = ((current_value / year_ago_value) - 1) * 100
            
            # Format date based on frequency
            if frequency == "quarterly":
                # Convert to YYYY-QN format
                month = current_date.month
                quarter = (month - 1) // 3 + 1
                date_fmt = f"{current_date.year}-Q{quarter}"
            else:
                date_fmt = obs["date"][:7]  # YYYY-MM
            
            yoy_data.append({
                "date": date_fmt,
                "value": round(yoy, 2)
            })
    
    return yoy_data


# -----------------------------------------------------------------------------
# Data Fetching and Merging
# -----------------------------------------------------------------------------

def fetch_country_data(code: str) -> Optional[Dict]:
    """
    Fetch CPI data for a single country.
    
    Returns dict with 'history' list of {"date": "YYYY-MM", "value": float}
    or None if fetch fails.
    """
    config = COUNTRIES[code]
    print(f"  Fetching {config['flag']} {config['name']}...", end=" ")
    
    try:
        if config.get("api") == "ECB":
            raw_data = fetch_ecb_series(config["series_id"])
            yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                       for obs in raw_data]
        elif config.get("api") == "BLS":
            # Direct BLS Public Data API — no FRED lag.
            try:
                raw_data = fetch_bls_series(config["series_id"])
                if not raw_data:
                    raise ValueError(f"No data returned from BLS for {config['series_id']}")
                yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
            except Exception as e:
                # Fall back to FRED if BLS API fails (transient outages, rate limit, etc.)
                if config.get("fred_series"):
                    print(f"(BLS failed: {e}; falling back to FRED)...", end=" ")
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        else:
            # FRED API - try primary series, fall back to alt if available
            series_id = config.get("fred_series")
            used_alt = False
            data_type = config.get("data_type", "index")
            frequency = config.get("frequency", "monthly")
            
            try:
                raw_data = fetch_fred_series(series_id)
                if not raw_data:
                    raise ValueError(f"No data returned for {series_id}")
            except Exception as e:
                # Try alternative series if available
                if config.get("fred_series_alt"):
                    print(f"(primary failed, trying alt series)...", end=" ")
                    series_id = config["fred_series_alt"]
                    raw_data = fetch_fred_series(series_id)
                    used_alt = True
                    # Alt series may have different data_type
                    # World Bank FPCPITOTLZG* series are annual YoY rates
                    if series_id.startswith("FPCPITOTLZG"):
                        data_type = "yoy"
                        frequency = "annual"
                    # OECD GYM659N series are monthly YoY rates
                    elif "GYM659N" in series_id:
                        data_type = "yoy"
                else:
                    raise e
            
            if data_type == "yoy":
                # Data is already YoY
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)} 
                           for obs in raw_data]
            else:
                # Calculate YoY from index
                yoy_data = calculate_yoy_from_index(raw_data, frequency)
        
        if yoy_data:
            latest = yoy_data[-1]
            print(f"✅ {len(yoy_data)} pts, latest: {latest['date']} = {latest['value']}%")
            return {
                "history": yoy_data,
                "latest": latest,
                "previous": yoy_data[-2] if len(yoy_data) > 1 else None
            }
        else:
            print("⚠️ No data")
            return None
            
    except Exception as e:
        print(f"❌ {e}")
        return None


def load_existing_data() -> Dict:
    """Load existing historical_cpi.json if it exists."""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


STEP_THRESHOLD_PP = 1.0  # YoY inflation rarely shifts >1pp month-over-month
ANOMALY_LOG: List[Dict] = []


def _prior_year_value(history: List[Dict], date: str) -> Optional[float]:
    """Value in prior year's same period, or None."""
    if '-Q' in date:
        year, q = date.split('-Q')
        prior = f"{int(year) - 1}-Q{q}"
    else:
        year, month = date.split('-')
        prior = f"{int(year) - 1}-{month}"
    for h in history:
        if h['date'] == prior:
            return h['value']
    return None


def _log_anomaly(code: str, date: str, value: float, prev_value: Optional[float],
                 prior_year: Optional[float], reasons: List[str]):
    ANOMALY_LOG.append({
        "country": code,
        "date": date,
        "value": value,
        "previous_value": prev_value,
        "prior_year_value": prior_year,
        "reasons": reasons,
    })


def detect_anomalies(code: str, new_point: Dict, prev_point: Optional[Dict], history: List[Dict]):
    """Append to ANOMALY_LOG if the new point looks suspicious."""
    date, value = new_point['date'], new_point['value']
    prev_value = prev_point['value'] if prev_point and isinstance(prev_point.get('value'), (int, float)) else None
    prior_year = _prior_year_value(history, date)
    reasons = []
    if prev_value is not None and abs(value - prev_value) > STEP_THRESHOLD_PP:
        reasons.append(f"step {value - prev_value:+.2f}pp > {STEP_THRESHOLD_PP}pp ({prev_value}% → {value}%)")
    if prior_year is not None and abs(value - prior_year) < 0.01:
        reasons.append(f"exactly matches prior-year same-period ({prior_year}%) — possible comparison-text miscapture")
    if reasons:
        _log_anomaly(code, date, value, prev_value, prior_year, reasons)


def merge_country_data(existing: Dict, fetched: Dict, code: str) -> Dict:
    """
    Merge fetched data with existing data for a country.
    
    Strategy:
    - Keep existing 'latest' and 'previous' if they're more recent than FRED
    - Add any new history points from FRED that we don't have
    - Preserve manually added fields (notes, source_url, etc.)
    """
    config = COUNTRIES[code]
    
    # Start with existing data or create new
    if code in existing and existing[code].get("history"):
        merged = existing[code].copy()
    else:
        merged = {
            "name": config["name"],
            "flag": config["flag"],
            "target": config["target"],
            "source": config["source"],
            "source_url": config.get("source_url", ""),
            "fred_series": config.get("fred_series", ""),
            "frequency": config["frequency"],
            "history": []
        }
    
    # Preserve notes if they exist
    if config.get("notes") and "notes" not in merged:
        merged["notes"] = config["notes"]
    
    if not fetched:
        return merged
    
    # Get existing dates for quick lookup
    existing_dates = {h["date"] for h in merged.get("history", [])}
    
    # Add new history points from FRED
    new_points = 0
    for point in fetched.get("history", []):
        if point["date"] not in existing_dates:
            # Anomaly check vs. existing history before appending
            hist_so_far = sorted(merged.get("history", []), key=lambda x: x["date"])
            prev = hist_so_far[-1] if hist_so_far else None
            detect_anomalies(code, point, prev, hist_so_far)
            merged.setdefault("history", []).append(point)
            new_points += 1
    
    # Sort history by date
    merged["history"] = sorted(merged.get("history", []), key=lambda x: x["date"])
    
    # Update latest/previous only if FRED has newer data
    if fetched.get("latest"):
        fred_latest_date = fetched["latest"]["date"]
        existing_latest_date = merged.get("latest", {}).get("date", "")
        
        if fred_latest_date > existing_latest_date:
            # FRED has newer data
            merged["latest"] = fetched["latest"]
            merged["previous"] = fetched.get("previous") or merged.get("previous")
            print(f"    → Updated latest: {fred_latest_date}")
        elif fred_latest_date < existing_latest_date:
            print(f"    → Kept manual data (FRED lags: {fred_latest_date} vs {existing_latest_date})")
    
    if new_points > 0:
        print(f"    → Added {new_points} history points")
    
    return merged


def fetch_and_merge(countries: List[str] = None, overwrite: bool = False) -> Dict:
    """
    Fetch data for specified countries and merge with existing.
    
    Args:
        countries: List of country codes, or None for all
        overwrite: If True, replace existing data entirely
    """
    if countries is None:
        countries = DISPLAY_ORDER
    
    print("=" * 60)
    print("Fetching CPI data from FRED/ECB APIs")
    print("=" * 60)
    
    existing = {} if overwrite else load_existing_data()
    
    for code in countries:
        if code not in COUNTRIES:
            print(f"  ⚠️ Unknown country code: {code}")
            continue
        
        fetched = fetch_country_data(code)
        existing[code] = merge_country_data(existing, fetched, code)
    
    # Ensure metadata exists
    if "metadata" not in existing:
        existing["metadata"] = {}
    existing["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    existing["metadata"]["source"] = "Official national statistical agencies"
    
    # Reorder keys for consistent output
    ordered = {"metadata": existing.pop("metadata", {})}
    for code in DISPLAY_ORDER:
        if code in existing:
            ordered[code] = existing.pop(code)
    ordered.update(existing)  # Any remaining
    
    return ordered


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch and merge CPI data from FRED/ECB APIs"
    )
    parser.add_argument(
        "--country", "-c",
        help="Fetch single country (e.g., US, UK)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing data instead of merging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving"
    )
    args = parser.parse_args()
    
    # Check for API key
    if not FRED_API_KEY:
        print("❌ FRED_API_KEY not set")
        print("   Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("   Set it: export FRED_API_KEY=your_key_here")
        sys.exit(1)
    
    # Determine which countries to fetch
    countries = [args.country.upper()] if args.country else None
    
    # Fetch and merge
    data = fetch_and_merge(countries, overwrite=args.overwrite)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for code in DISPLAY_ORDER:
        if code in data and code != "metadata":
            country = data[code]
            latest = country.get("latest", {})
            if latest:
                target = country.get("target")
                target_str = f"{target}%" if target else "N/A"
                value = latest.get("value", 0)
                date = latest.get("date", "?")
                print(f"{country.get('flag', '')} {code}: {value:5.1f}% ({date}) target: {target_str}")
            else:
                print(f"{country.get('flag', '')} {code}: No data")
    
    # Save
    if args.dry_run:
        print("\n[DRY RUN] Would save to:", DATA_FILE)
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved: {DATA_FILE}")

    # Anomaly report
    if ANOMALY_LOG:
        print("\n" + "=" * 60)
        print(f"⚠  {len(ANOMALY_LOG)} ANOMALIES DETECTED")
        print("=" * 60)
        for a in ANOMALY_LOG:
            print(f"  {a['country']} {a['date']} = {a['value']}%")
            for reason in a['reasons']:
                print(f"    - {reason}")
        anomaly_file = OUTPUT_DIR / "cpi_anomalies.json"
        if not args.dry_run:
            with open(anomaly_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "detected_at": datetime.now().isoformat(timespec='seconds'),
                    "threshold_pp": STEP_THRESHOLD_PP,
                    "anomalies": ANOMALY_LOG,
                }, f, indent=2, ensure_ascii=False)
            print(f"\n   Logged to: {anomaly_file}")
        sys.exit(2)  # non-zero so CI / cron can flag


if __name__ == "__main__":
    main()
