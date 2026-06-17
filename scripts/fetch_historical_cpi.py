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
TARGETS_FILE = OUTPUT_DIR / "targets.json"

_TARGETS_CACHE: Optional[Dict] = None


def get_target(code: str) -> Optional[float]:
    """Inflation target midpoint from docs/data/targets.json — the single
    source of truth for targets (#82). Returns None when the country has no
    entry; never falls back to a hardcoded value (that duplication is what
    let ZA's pre-Nov-2025 target linger in historical_cpi.json for months).
    """
    global _TARGETS_CACHE
    if _TARGETS_CACHE is None:
        try:
            with open(TARGETS_FILE) as f:
                _TARGETS_CACHE = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"WARNING: could not load {TARGETS_FILE}: {e} — "
                  f"target fields will be written as null")
            _TARGETS_CACHE = {}
    entry = _TARGETS_CACHE.get(code) or {}
    return entry.get("value")

# -----------------------------------------------------------------------------
# Country Configuration - All 15 Countries
# -----------------------------------------------------------------------------

COUNTRIES = {
    "US": {
        "name": "United States",
        "flag": "🇺🇸",
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
        "source": "ONS",
        "source_url": "https://www.ons.gov.uk/economy/inflationandpriceindices",
        "api": "ONS",
        "series_id": "d7g7",  # CPI ALL ITEMS 12-month rate (already YoY)
        "fred_series": "GBRCPIALLMINMEI",  # FRED fallback if ONS API fails
        "frequency": "monthly",
        "data_type": "yoy",  # ONS d7g7 is already YoY
        "lag_months": 2,  # FRED typically lags ONS by 1-2 months
    },
    "CA": {
        "name": "Canada",
        "flag": "🇨🇦",
        "source": "Statistics Canada",
        "source_url": "https://www.statcan.gc.ca/",
        "api": "StatCan",
        "series_id": 41690973,  # All-items CPI, monthly NSA index (vector V41690973)
        "fred_series": "CANCPIALLMINMEI",  # FRED fallback if StatCan API fails
        "frequency": "monthly",
        "data_type": "index",
        "lag_months": 2,
    },
    "AU": {
        "name": "Australia",
        "flag": "🇦🇺",
        "source": "ABS",
        "source_url": "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/",
        "api": "ABS",  # primary national source (monthly CPI indicator); fresher than FRED's quarterly OECD relay (#50)
        "fred_series": "AUSCPIALLQINMEI",  # OECD quarterly index — fallback only
        "frequency": "monthly",
        "data_type": "yoy",  # ABS Data API returns the YoY rate directly
        "lag_months": 3,
        "notes": "ABS publishes a monthly CPI indicator (since late 2025); FRED's OECD series is still quarterly and lags.",
    },
    "NZ": {
        "name": "New Zealand",
        "flag": "🇳🇿",
        "source": "Stats NZ",
        "source_url": "https://www.stats.govt.nz/indicators/consumers-price-index-cpi/",
        "fred_series": "NZLCPIALLQINMEI",  # OECD quarterly index
        "frequency": "quarterly",
        "data_type": "index",
    },
    "ZA": {
        "name": "South Africa",
        "flag": "🇿🇦",
        "source": "Stats SA",
        "source_url": "https://www.statssa.gov.za/",
        "api": "StatsSA",  # primary national source (P0141 PDF); FRED-OECD lags 6-12mo (#53)
        "fred_series": "ZAFCPIALLMINMEI",  # OECD index — fallback only
        "frequency": "monthly",
        "data_type": "yoy",  # P0141 publishes the annual rate directly
        "lag_months": 6,  # FRED significantly lags Stats SA
        "notes": "SARB target changed to 3% in 2025",
    },
    "JP": {
        "name": "Japan",
        "flag": "🇯🇵",
        "source": "MIC",
        "source_url": "https://www.stat.go.jp/english/data/cpi/",
        "api": "eStat",  # primary national source: e-Stat getStatsData (#51)
        "estat_stats_code": "00200573",  # Consumer Price Index (Statistics Bureau)
        "estat_stats_data_id": "0003427113",  # 2020-Base Consumer Price Index (main table)
        # Dimensions resolved from getMetaInfo: area 00000 = All Japan, cat01
        # 0001 = All items (NOT 0161 "less fresh food" = core). The year-on-year
        # tab code is picked from the response metadata by name at runtime.
        "estat_cdArea": "00000",
        "estat_cdCat01": "0001",
        "fred_series": "JPNCPALTT01IXNBM",  # COICOP 2018 index, monthly — fallback only
        "fred_series_alt": "JPNCPIALLMINMEI",  # COICOP 1999 fallback (discontinued Jun 2021 but may still serve data)
        "frequency": "monthly",
        "data_type": "index",
        "notes": "Primary: Statistics Bureau all-items CPI (YoY) via e-Stat API. Fallback: FRED COICOP 2018/1999 index.",
    },
    "CN": {
        "name": "China",
        "flag": "🇨🇳",
        "source": "NBS",
        "source_url": "https://www.stats.gov.cn/english/",
        "api": "NBS",  # primary national source (English CPI press release) (#56)
        "fred_series": "CHNCPIALLMINMEI",  # OECD index — fallback only
        "frequency": "monthly",
        "data_type": "yoy",  # press release states the YoY rate directly
    },
    "IN": {
        "name": "India",
        "flag": "🇮🇳",
        "source": "MOSPI",
        "source_url": "https://www.mospi.gov.in/",
        "api": "MoSPI",  # primary national source (CPI press release PDF) (#57)
        "fred_series": "INDCPIALLMINMEI",  # OECD index — fallback only
        "frequency": "monthly",
        "data_type": "yoy",  # press release states the YoY rate directly
    },
    "KR": {
        "name": "South Korea",
        "flag": "🇰🇷",
        "source": "KOSTAT",
        "source_url": "https://kostat.go.kr/",
        "fred_series": "KORCPALTT01IXNBM",  # COICOP 2018 index, monthly
        "fred_series_alt": "KORCPIALLMINMEI",  # COICOP 1999 fallback (discontinued Nov 2023)
        "frequency": "monthly",
        "data_type": "index",
        "notes": "Primary: COICOP 2018 index. Fallback: COICOP 1999 (discontinued Nov 2023).",
    },
    "SG": {
        "name": "Singapore",
        "flag": "🇸🇬",
        "source": "SingStat",
        "source_url": "https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/consumer-price-index/latest-news-data",
        "api": "SingStat",  # primary national source: TableBuilder API (#52)
        # Auto-selects the monthly "Percent Change ... Over Corresponding Period
        # Of Previous Year" (YoY) table and reads its headline "All Items" row
        # (distinct from MAS core). resourceId left null → resolved by title at
        # runtime so base-year revisions don't break it (TableBuilder is keyless).
        "singstat_resource_id": None,
        "singstat_row": "All Items",
        "fred_series": "FPCPITOTLZGSGP",  # World Bank annual YoY — fallback only
        "frequency": "monthly",
        "data_type": "yoy",  # SingStat "Percent Change ... Previous Year" is already YoY
        "notes": "Primary: SingStat TableBuilder CPI All-Items YoY (monthly). Fallback: FRED World Bank annual.",
    },
}

# Display order for output
DISPLAY_ORDER = ['US', 'EA', 'UK', 'CA', 'AU', 'NZ', 'ZA', 'JP', 'CN', 'IN', 'KR', 'SG']


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


def fetch_ons_series(timeseries_id: str, dataset: str = "mm23") -> List[Dict]:
    """Fetch a YoY rate series from the ONS Beta API.

    Series IDs of interest:
      - 'd7g7' on dataset 'mm23' = CPI ALL ITEMS, 12-month rate (UK CPI YoY).

    Returns observations as a list of {"date": "YYYY-MM-DD", "value": float}
    sorted ascending. Values are already YoY rates (no index calc needed).
    """
    url = (f"https://api.beta.ons.gov.uk/v1/data"
           f"?uri=/economy/inflationandpriceindices/timeseries/{timeseries_id}/{dataset}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    months = data.get("months", [])
    observations = []
    for m in months:
        # 'date' format: '2026 MAR' — parse to YYYY-MM-01
        date_str = m.get("date", "")
        try:
            year, mon_abbr = date_str.split()
            month_num = {
                "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
                "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
            }[mon_abbr.upper()]
        except (ValueError, KeyError):
            continue
        try:
            value = float(m.get("value"))
        except (TypeError, ValueError):
            continue
        observations.append({
            "date": f"{int(year):04d}-{month_num:02d}-01",
            "value": value,
        })

    observations.sort(key=lambda x: x["date"])
    return observations


def fetch_statcan_series(vector_id: int, latest_n: int = 240) -> List[Dict]:
    """Fetch an index series from the Statistics Canada Web Data Service.

    Vector IDs of interest:
      - 41690973 = All-items CPI, monthly, NSA, Canada (index, 2002=100).

    Returns observations as a list of {"date": "YYYY-MM-DD", "value": float}.
    Caller computes YoY from the index (same path as BLS).
    """
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"
    payload = [{"vectorId": int(vector_id), "latestN": int(latest_n)}]
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not data or data[0].get("status") != "SUCCESS":
        msg = data[0].get("object") if data else "no response"
        raise RuntimeError(f"StatCan WDS error: {msg}")

    points = data[0].get("object", {}).get("vectorDataPoint", [])
    observations = []
    for p in points:
        ref = p.get("refPer", "")  # 'YYYY-MM-DD'
        if not ref:
            continue
        try:
            value = float(p.get("value"))
        except (TypeError, ValueError):
            continue
        observations.append({"date": ref, "value": value})

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


def fetch_eurostat_flash_release() -> List[Dict]:
    """Euro-area HICP *flash* estimate from the Eurostat euro-indicators press
    release (#60). The bulk ECB/Eurostat datasets lag the flash, so we read the
    headline rate straight from the release titled "Euro area annual inflation
    up to/down to X.X%". The release URL is date-slugged (.../w/N-DDMMYYYY-ap),
    so we discover the latest from the euro-indicators listing (newest first)
    and take the first page that is the HICP flash. Returns a single
    ``[{date, value}]`` for the flash month, or [] on any structure change.
    """
    import re as _re
    headers = {"User-Agent": _BROWSER_UA,
               "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
               "Accept-Language": "en"}
    months = {name[:3].lower(): i for i, name in enumerate(_MONTH_NAMES) if name}
    listing = "https://ec.europa.eu/eurostat/web/products-euro-indicators"
    try:
        lr = requests.get(listing, headers=headers, timeout=40)
        codes = _re.findall(r'/w/(\d+-\d{8}-[a-z]{2})', lr.text)
    except Exception as e:
        print(f"  ⚠️  Eurostat listing error: {type(e).__name__}: {e}")
        return []
    seen = set()
    ordered = [c for c in codes if not (c in seen or seen.add(c))]
    rel_base = "https://ec.europa.eu/eurostat/en/web/products-euro-indicators/w/"
    # "up to 3.2%" / "down to 1.9%" / "stable at 2.0%" — capture the headline %.
    val_re = _re.compile(r"Euro area annual inflation\D{0,24}?(\d+\.\d+)\s*%", _re.I)
    for code in ordered[:8]:
        try:
            pr = requests.get(rel_base + code, headers=headers, timeout=40)
            if pr.status_code != 200:
                continue
            txt = _re.sub(r"<[^>]+>", " ", pr.text)
            txt = _re.sub(r"\s+", " ", txt)
        except Exception:
            continue
        vm = val_re.search(txt)
        if not vm:
            continue  # not the HICP flash release
        value = float(vm.group(1))
        mm = _re.search(r"annual rate in (\w+)", txt)  # e.g. "...rate in May (10.9%..."
        dm = _re.match(r"\d+-(\d{2})(\d{2})(\d{4})-", code)
        if not mm or not dm:
            continue
        mi = months.get(mm.group(1)[:3].lower())
        if not mi:
            continue
        rel_month, rel_year = int(dm.group(2)), int(dm.group(3))
        year = rel_year - 1 if mi > rel_month else rel_year  # handle Dec→Jan rollover
        if not (-5.0 <= value <= 30.0):
            return []
        print(f"  ℹ️  Eurostat HICP flash release {code}: {year}-{mi:02d} = {value}%")
        return [{"date": f"{year:04d}-{mi:02d}-01", "value": round(value, 2)}]
    print("    [diag] Eurostat flash: no inflation release found in recent listing")
    return []


# -----------------------------------------------------------------------------
# YoY Calculation
# -----------------------------------------------------------------------------

def fetch_abs_cpi_series() -> List[Dict]:
    """Fetch Australia headline CPI (monthly indicator, YoY %) from the ABS Data API (#50).

    Public SDMX REST endpoint — the *Data* API (data.api.abs.gov.au/rest/data)
    is keyless; only the separate *Indicator* API needs a key. Dataflow
    ABS,CPI,2.0.0. Datakey positions are MEASURE.INDEX.TSEST.REGION.FREQ; we
    pin INDEX=10001 (All groups CPI), TSEST=10 (Original), REGION=50 (Australia),
    FREQ=M (monthly) and wildcard MEASURE, then pick the YoY "percentage change
    ... previous year" measure by its label from the CSV-with-labels output.

    Values are already YoY (no index calc). Returns ascending
    [{"date": "YYYY-MM-01", "value": float}]. Heavily logged because the ABS
    response shape is only observable from a network that can reach it (#50),
    and we must confirm ABS is reachable from GitHub runners at all.
    """
    import csv as _csv
    import io as _io
    url = ("https://data.api.abs.gov.au/rest/data/ABS,CPI,2.0.0/"
           ".10001.10.50.M?startPeriod=2024&format=csvfilewithlabels")
    resp = requests.get(url, timeout=45, headers={"Accept": "text/csv"})
    resp.raise_for_status()
    text = resp.text
    reader = _csv.DictReader(_io.StringIO(text))
    fields = reader.fieldnames or []
    print(f"    [diag] ABS reachable, {len(text)} bytes; columns={fields}")

    # csvfilewithlabels emits BOTH an UPPERCASE code column (e.g. MEASURE = 1..7)
    # and a Title-case label column (e.g. Measure = "Percentage Change ..."). We
    # match the YoY measure on the *label* column; periods/values use the code
    # columns (TIME_PERIOD is ISO "YYYY-MM", OBS_VALUE is numeric).
    def find_col(*needles):
        for f in fields:
            if all(n in f.lower() for n in needles):
                return f
        return None

    def find_label_col(*needles):
        cands = [f for f in fields if all(n in f.lower() for n in needles)]
        for f in cands:           # prefer a human label (not the all-caps code col)
            if f != f.upper():
                return f
        return cands[0] if cands else None

    measure_col = find_label_col("measure")
    period_col = find_col("time_period") or find_col("time", "period")
    value_col = find_col("obs_value") or find_col("observation", "value")

    rows = list(reader)
    measures = sorted({(r.get(measure_col) or "").strip() for r in rows}) if measure_col else []
    print(f"    [diag] measure_col={measure_col!r} period_col={period_col!r} "
          f"value_col={value_col!r}; measure labels={measures}")

    obs = []
    if measure_col and period_col and value_col:
        for r in rows:
            label = (r.get(measure_col) or "").lower()
            if "percentage change" in label and "previous year" in label:
                period = (r.get(period_col) or "").strip()
                if len(period) != 7 or period[4] != "-":  # expect YYYY-MM
                    continue
                try:
                    value = float(r.get(value_col))
                except (TypeError, ValueError):
                    continue
                obs.append({"date": f"{period}-01", "value": round(value, 2)})
    obs.sort(key=lambda x: x["date"])
    if obs:
        print(f"    [diag] ABS YoY parsed: latest {obs[-1]}")
    else:
        print("    [diag] ABS: no YoY rows parsed (see measures above)")
    return obs


def fetch_abs_quarterly_yoy() -> List[Dict]:
    """Fetch Australia's quarterly CPI as YoY % from the ABS Data API (#109).

    AU's underlying historical series is quarterly, and ABS's own quarterly CPI
    is current (FRED's OECD relay AUSCPIALLQINMEI lags ~5 quarters). Same keyless
    dataflow as the monthly indicator (ABS,CPI,2.0.0) with FREQ=Q. The quarterly
    flow exposes index numbers and QoQ change but NO ready YoY measure, so we
    pull the All-groups index (INDEX=10001, TSEST=10 Original, REGION=50) and
    compute YoY = this quarter / the same quarter a year earlier. Periods are
    native "YYYY-Qn". Returns ascending [{"date": "YYYY-Qn", "value": float}].
    """
    import csv as _csv
    import io as _io
    url = ("https://data.api.abs.gov.au/rest/data/ABS,CPI,2.0.0/"
           ".10001.10.50.Q?startPeriod=2014&format=csvfilewithlabels")
    resp = requests.get(url, timeout=45, headers={"Accept": "text/csv"})
    resp.raise_for_status()
    rows = list(_csv.DictReader(_io.StringIO(resp.text)))
    fields = list(rows[0].keys()) if rows else []
    print(f"    [diag] ABS quarterly reachable, {len(rows)} rows")

    def label_col(*needles):
        cands = [f for f in fields if all(n in f.lower() for n in needles)]
        for f in cands:           # prefer the human label, not the all-caps code col
            if f != f.upper():
                return f
        return cands[0] if cands else None

    def code_col(*needles):
        for f in fields:
            if all(n in f.lower() for n in needles):
                return f
        return None

    measure_col = label_col("measure")
    period_col = code_col("time_period") or code_col("time", "period")
    value_col = code_col("obs_value") or code_col("observation", "value")

    # Build the quarterly index series {"YYYY-Qn": index}.
    index_by_q = {}
    if measure_col and period_col and value_col:
        for r in rows:
            if "index number" not in (r.get(measure_col) or "").lower():
                continue
            period = (r.get(period_col) or "").strip()   # YYYY-Qn
            if len(period) != 7 or "-Q" not in period:
                continue
            try:
                index_by_q[period] = float(r.get(value_col))
            except (TypeError, ValueError):
                continue

    out = []
    for period in sorted(index_by_q):
        year, quarter = period.split("-Q")
        year_ago = f"{int(year) - 1}-Q{quarter}"
        prev = index_by_q.get(year_ago)
        if prev:
            out.append({"date": period,
                        "value": round((index_by_q[period] / prev - 1) * 100, 2)})
    if out:
        print(f"    [diag] ABS quarterly YoY: {len(out)} pts, latest {out[-1]}")
    else:
        print("    [diag] ABS quarterly: no YoY computed (index series empty?)")
    return out


_BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
_MONTH_NAMES = [None, "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]


def fetch_statssa_cpi_series() -> List[Dict]:
    """Fetch South Africa headline CPI (YoY %) from the Stats SA P0141 release (#53).

    Stats SA has no clean public API; the monthly CPI statistical release (P0141)
    is a PDF at a predictable path:
        https://www.statssa.gov.za/publications/P0141/P0141<MonthName><Year>.pdf
    We walk back from the current month to the latest published release and parse
    the headline annual rate. DIAGNOSTIC PASS: this both confirms whether
    statssa.gov.za is reachable from GitHub runners (the IBGE lesson) and dumps
    the headline text so the parser can anchor precisely. Returns [] for now so
    the caller falls back to FRED.
    """
    import io as _io
    from datetime import date
    try:
        import pdfplumber
    except ImportError:
        print("(pdfplumber not installed)", end=" ")
        return []

    headers = {"User-Agent": _BROWSER_UA, "Accept": "application/pdf,*/*"}
    today = date.today()
    y, m = today.year, today.month
    pdf_bytes = used_url = None
    for _ in range(8):
        url = f"https://www.statssa.gov.za/publications/P0141/P0141{_MONTH_NAMES[m]}{y}.pdf"
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                pdf_bytes, used_url = r.content, url
                break
            print(f"[diag] {url} -> {r.status_code}", end="  ")
        except Exception as e:
            print(f"[diag] {url} -> {type(e).__name__}", end="  ")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    if not pdf_bytes:
        print("[diag] StatsSA: no P0141 PDF reachable")
        return []

    print(f"  ℹ️  Stats SA P0141: {used_url} ({len(pdf_bytes)} bytes)")
    import re as _re
    try:
        with pdfplumber.open(_io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages[:4])
    except Exception as e:
        print(f"  ⚠️  pdfplumber error: {type(e).__name__}: {e}")
        return []
    text = _re.sub(r"\s+", " ", text)

    # Anchor on the standard P0141 headline sentence, e.g.:
    #   "Annual consumer price inflation was 4,0% in April 2026, up from 3,1%
    #    in March 2026."
    # which also states the previous month, so we capture both for a little
    # history. SA uses decimal commas. This is the headline all-items CPI YoY —
    # we never touch the goods/services/category lines (CLAUDE.md #2).
    months = {name.lower(): i for i, name in enumerate(_MONTH_NAMES) if name}
    m = _re.search(
        r"[Aa]nnual consumer price inflation was (\d+,\d+)% in (\w+) (\d{4})"
        r"(?:.{0,40}?from (\d+,\d+)% in (\w+) (\d{4}))?",
        text,
    )
    obs = []

    def _add(val, mon, yr):
        mi = months.get((mon or "").lower())
        try:
            v = float(val.replace(",", "."))
        except (TypeError, ValueError):
            return
        if mi and -5.0 <= v <= 30.0:
            obs.append({"date": f"{int(yr):04d}-{mi:02d}-01", "value": round(v, 2)})

    if m:
        _add(m.group(1), m.group(2), m.group(3))
        if m.group(4):
            _add(m.group(4), m.group(5), m.group(6))

    if not obs:
        print("  ⏸️  scrape_statssa: headline sentence not found; preserving curated ZA")
        idx = text.lower().find("annual consumer price")
        if idx != -1:
            print("      [diag] near: " + text[idx:idx + 140])
        return []

    obs.sort(key=lambda x: x["date"])
    print(f"  ✅ Stats SA headline CPI: {obs}")
    return obs


def fetch_mospi_cpi_series() -> List[Dict]:
    """India headline CPI (YoY %) from the MoSPI CPI press release PDF (#57).

    MoSPI publishes a monthly "CPI Press Release of <Month> <Year>" PDF under
    /uploads/PressRelease/. We walk back to the latest release and parse the
    headline All-India CPI (General) year-on-year inflation rate. DIAGNOSTIC
    PASS: confirms mospi.gov.in is reachable from GitHub runners and dumps the
    headline text so the parser can anchor precisely. Returns [] (→ FRED).
    """
    import io as _io
    import re as _re
    from datetime import date
    try:
        import pdfplumber
    except ImportError:
        print("(pdfplumber not installed)", end=" ")
        return []

    headers = {"User-Agent": _BROWSER_UA, "Accept": "application/pdf,*/*"}
    base = "https://www.mospi.gov.in/uploads/PressRelease/"
    today = date.today()
    y, m = today.year, today.month
    pdf_bytes = used_url = None
    for _ in range(8):
        for tmpl in (f"CPI Press Release of {_MONTH_NAMES[m]} {y}.pdf",
                     f"CPI Press Release {_MONTH_NAMES[m]} {y}.pdf"):
            url = base + tmpl.replace(" ", "%20")
            try:
                r = requests.get(url, headers=headers, timeout=30)
                if r.status_code == 200 and r.content[:4] == b"%PDF":
                    pdf_bytes, used_url = r.content, url
                    break
                print(f"[diag] {tmpl} -> {r.status_code}", end="  ")
            except Exception as e:
                print(f"[diag] {tmpl} -> {type(e).__name__}", end="  ")
        if pdf_bytes:
            break
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    if not pdf_bytes:
        print("[diag] MoSPI: no CPI press release reachable")
        return []

    print(f"  ℹ️  MoSPI press release: {used_url} ({len(pdf_bytes)} bytes)")
    try:
        with pdfplumber.open(_io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages[:3])
    except Exception as e:
        print(f"  ⚠️  pdfplumber error: {type(e).__name__}: {e}")
        return []
    text = _re.sub(r"\s+", " ", text)

    # Anchor on the headline General-CPI sentence, e.g.:
    #   "Retail inflation based on Consumer Price Index in April, 2026 is 3.48%"
    # This phrasing is unique to the All-India headline CPI; the food line uses
    # "Consumer Food Price Index", so we never confuse headline with food/fuel/
    # housing sub-indices (CLAUDE.md #2). India uses decimal points.
    months = {name.lower(): i for i, name in enumerate(_MONTH_NAMES) if name}
    m = _re.search(
        r"Retail inflation based on Consumer Price Index in (\w+),?\s*(\d{4}) is (\d+\.\d+)\s*%",
        text,
    )
    obs = []
    if m:
        mi = months.get(m.group(1).lower())
        v = float(m.group(3))
        if mi and -5.0 <= v <= 30.0:
            obs.append({"date": f"{int(m.group(2)):04d}-{mi:02d}-01", "value": round(v, 2)})

    if not obs:
        print("  ⏸️  scrape_mospi: headline 'Retail inflation' sentence not found; preserving curated IN")
        return []
    print(f"  ✅ MoSPI headline CPI: {obs}")
    return obs


ESTAT_BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"


def fetch_estat_cpi_series(config: Dict) -> List[Dict]:
    """Japan headline all-items CPI (YoY %) from the e-Stat API (#51).

    Japan's all-items monthly CPI is not published in any keyless machine-
    readable form (the Statistics Bureau funnels its statistical tables through
    e-Stat), so we use the official e-Stat ``getStatsData`` JSON API. This
    requires a free application id supplied via the ``ESTAT_APP_ID`` secret.

    Two phases:
      * No ``estat_stats_data_id`` configured yet → DISCOVERY: call
        ``getStatsList`` for the CPI stats code and log the candidate table ids
        + titles so the exact national all-items monthly table can be pinned.
      * Pinned id → fetch + parse the all-items (総合) year-on-year series.

    Returns [] (→ FRED) when the appId is absent or on any structure change.
    """
    import re as _re
    app_id = os.environ.get("ESTAT_APP_ID")
    if not app_id:
        print("(ESTAT_APP_ID not set)", end=" ")
        return []
    headers = {"User-Agent": _BROWSER_UA, "Accept": "application/json"}
    stats_data_id = config.get("estat_stats_data_id")

    # --- DISCOVERY phase: until the dimension codes (which area = All Japan,
    # which tab = year-on-year, which item = all-items) are pinned in config,
    # list the CPI tables and dump the pinned table's getMetaInfo so the codes
    # can be read off and locked in. ---
    if not config.get("estat_cdCat01"):
        if not stats_data_id:
            params = {"appId": app_id, "statsCode": config.get("estat_stats_code", "00200573"),
                      "searchKind": "1", "lang": "E", "limit": "100"}
            try:
                j = requests.get(f"{ESTAT_BASE}/getStatsList", params=params,
                                 headers=headers, timeout=40).json()
            except Exception as e:
                print(f"[diag] e-Stat getStatsList error: {type(e).__name__}: {e}")
                return []
            tables = (j.get("GET_STATS_LIST", {}).get("DATALIST_INF", {}) or {}).get("TABLE_INF", [])
            if isinstance(tables, dict):
                tables = [tables]
            print(f"    [diag] e-Stat getStatsList: {len(tables)} CPI table(s)")
            for t in tables:
                tt = t.get("TITLE")
                tt = tt.get("$", "") if isinstance(tt, dict) else (tt or "")
                print(f"      [diag] id={t.get('@id')} :: {str(tt)[:90]}")
            return []
        # Meta-dump the pinned table's dimensions + codes.
        try:
            j = requests.get(f"{ESTAT_BASE}/getMetaInfo",
                             params={"appId": app_id, "statsDataId": stats_data_id, "lang": "E"},
                             headers=headers, timeout=40).json()
        except Exception as e:
            print(f"[diag] e-Stat getMetaInfo error: {type(e).__name__}: {e}")
            return []
        objs = (j.get("GET_META_INFO", {}).get("METADATA_INF", {}).get("CLASS_INF", {}) or {}).get("CLASS_OBJ", [])
        if isinstance(objs, dict):
            objs = [objs]
        print(f"    [diag] e-Stat getMetaInfo {stats_data_id}: {len(objs)} dimension(s)")
        for o in objs:
            codes = o.get("CLASS", [])
            if isinstance(codes, dict):
                codes = [codes]
            print(f"      [diag] dim @id={o.get('@id')} name={o.get('@name')} ({len(codes)} codes)")
            # Show codes most likely to be the anchors we need.
            for c in codes:
                nm = c.get("@name", "")
                if any(k in nm for k in ("All Japan", "All items", "year-on-year",
                                          "Year-on-year", "全国", "総合", "前年同月")):
                    print(f"        [diag] code={c.get('@code')} :: {nm[:60]}")
        return []

    # --- DATA phase: fetch all-items / All-Japan and parse the YoY series. ---
    params = {"appId": app_id, "statsDataId": stats_data_id, "lang": "E",
              "metaGetFlg": "Y", "cntGetFlg": "N",
              "cdArea": config["estat_cdArea"], "cdCat01": config["estat_cdCat01"]}
    try:
        r = requests.get(f"{ESTAT_BASE}/getStatsData", params=params,
                         headers=headers, timeout=60)
        j = r.json()
    except Exception as e:
        print(f"  ⚠️  e-Stat getStatsData error: {type(e).__name__}: {e}")
        return []

    sd = j.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {})
    values = (sd.get("DATA_INF", {}) or {}).get("VALUE", [])
    if isinstance(values, dict):
        values = [values]
    if not values:
        result = j.get("GET_STATS_DATA", {}).get("RESULT", {})
        print(f"  ⏸️  e-Stat returned no VALUEs (status {result.get('STATUS')}: "
              f"{result.get('ERROR_MSG')}); preserving curated JP")
        return []

    classes = (sd.get("CLASS_INF", {}) or {}).get("CLASS_OBJ", [])
    if isinstance(classes, dict):
        classes = [classes]
    time_labels, tab_names = {}, {}
    for cls in classes:
        items = cls.get("CLASS", [])
        if isinstance(items, dict):
            items = [items]
        if cls.get("@id") == "time":
            for it in items:
                time_labels[it.get("@code")] = it.get("@name", "")
        elif cls.get("@id") == "tab":
            for it in items:
                tab_names[it.get("@code")] = it.get("@name", "")

    # The table carries 3 tabs (index / change over the month / change over the
    # year). Pick the year-on-year one by name — never assume a fixed code, and
    # never confuse it with the month-on-month tab (CLAUDE.md #2).
    yoy_tab = next((c for c, nm in tab_names.items()
                    if "year" in nm.lower() and "month" not in nm.lower()), None)
    if not yoy_tab:
        print(f"  ⏸️  e-Stat: could not identify year-on-year tab in {tab_names}; preserving JP")
        return []

    def _year_month(code: str, label: str):
        # Prefer the human label (English e-Stat: "2026/4"); fall back to the
        # 10-digit monthly time code (e.g. 2026000404 = Apr 2026).
        mm = _re.search(r"(\d{4})\D+(\d{1,2})\b", label or "")
        if mm:
            return int(mm.group(1)), int(mm.group(2))
        if code and len(code) == 10 and code.isdigit() and code[8:10] != "00":
            return int(code[:4]), int(code[8:10])
        return None, None

    obs = []
    for v in values:
        if v.get("@tab") != yoy_tab:
            continue
        code = v.get("@time", "")
        y, mth = _year_month(code, time_labels.get(code, ""))
        if not y or not mth or not (1 <= mth <= 12):
            continue
        try:
            val = float(v.get("$"))
        except (TypeError, ValueError):
            continue
        if -10.0 <= val <= 30.0:
            obs.append({"date": f"{y:04d}-{mth:02d}-01", "value": round(val, 2)})

    if not obs:
        print("  ⏸️  e-Stat: no all-items YoY rows parsed; preserving curated JP")
        return []
    obs.sort(key=lambda o: o["date"])
    print(f"  ✅ e-Stat all-items CPI YoY: {len(obs)} pts, latest {obs[-1]}")
    return obs


def fetch_singstat_cpi_series(config: Dict) -> List[Dict]:
    """Singapore headline CPI All-Items (YoY %) from the SingStat TableBuilder
    API (#52). Keyless JSON. SingStat publishes a ready-made monthly table
    "Percent Change In Consumer Price Index (CPI) Over Corresponding Period Of
    Previous Year" (i.e. YoY); we auto-select it by title (robust to base-year
    revisions) and read its "All Items" row — the headline, distinct from MAS
    core (CLAUDE.md #2). Returns [] (→ FRED) on any structure change.
    """
    import re as _re
    base = "https://tablebuilder.singstat.gov.sg/api/table"
    headers = {"User-Agent": _BROWSER_UA, "Accept": "application/json"}
    anchor = (config.get("singstat_row") or "all items").strip().lower()
    mon3 = {name[:3].lower(): i for i, name in enumerate(_MONTH_NAMES) if name}

    def _search_records():
        s = requests.get(f"{base}/resourceid",
                         params={"keyword": "consumer price index", "searchOption": "all"},
                         headers=headers, timeout=40)
        dnode = s.json().get("Data")
        if isinstance(dnode, dict):
            return dnode.get("records") or dnode.get("Records") or []
        return dnode if isinstance(dnode, list) else []

    def _ym(key: str):
        s = (key or "").strip()
        ym = _re.search(r"(19|20)\d{2}", s)
        if not ym:
            return None, None
        year = int(ym.group(0))
        am = _re.search(r"[A-Za-z]{3,}", s)
        if am:
            mth = mon3.get(am.group(0)[:3].lower())
        else:
            nm = _re.search(r"\b(\d{1,2})\b", s.replace(ym.group(0), "", 1))
            mth = int(nm.group(1)) if nm else None
        return (year, mth) if (mth and 1 <= mth <= 12) else (None, None)

    # Resolve the resourceId: an explicit config override, else auto-select the
    # monthly YoY ("Over Corresponding Period Of Previous Year") CPI table,
    # preferring the most recent base year.
    rid = config.get("singstat_resource_id")
    if not rid:
        try:
            recs = _search_records()
        except Exception as e:
            print(f"  ⚠️  SingStat search error: {type(e).__name__}: {e}")
            return []
        cands = []
        for r_ in recs:
            if not isinstance(r_, dict):
                continue
            title = str(r_.get("title") or r_.get("Title") or "")
            t = title.lower()
            if ("over corresponding period of previous year" in t and "monthly" in t
                    and "household income" not in t):
                by = _re.search(r"(\d{4})\s+as base year", t)
                cands.append((int(by.group(1)) if by else 0, r_.get("id") or r_.get("ID"), title))
        if not cands:
            print(f"    [diag] SingStat: no monthly YoY CPI table among {len(recs)} results; "
                  f"sample={[str(x.get('title'))[:60] for x in recs[:6] if isinstance(x, dict)]}")
            return []
        cands.sort(reverse=True)  # highest base year first
        _, rid, title = cands[0]
        print(f"  ℹ️  SingStat auto-selected {rid} :: {title[:80]}")

    try:
        r = requests.get(f"{base}/tabledata/{rid}", headers=headers, timeout=60)
        j = r.json()
    except Exception as e:
        print(f"  ⚠️  SingStat tabledata error: {type(e).__name__}: {e}")
        return []

    data = j.get("Data")
    if not isinstance(data, dict):
        print(f"    [diag] SingStat {rid}: Data is {type(data).__name__} "
              f"(StatusCode={j.get('StatusCode')}, Msg={str(j.get('Message'))[:80]})")
        return []
    rows = data.get("row")
    if not isinstance(rows, list) or not rows:
        print(f"    [diag] SingStat {rid}: no rows ('{str(data.get('title'))[:60]}')")
        return []

    target = next((row for row in rows
                   if (row.get("rowText") or "").strip().lower() == anchor), None)
    if target is None:
        target = next((row for row in rows
                       if anchor in (row.get("rowText") or "").strip().lower()), None)
    if target is None:
        print(f"    [diag] '{anchor}' row not found; labels: "
              f"{[ (row.get('rowText') or '')[:24] for row in rows[:12] ]}")
        return []

    obs = []
    for c in target.get("columns", []) or []:
        y, mth = _ym(c.get("key", ""))
        if not y:
            continue
        raw = c.get("value")
        if raw in (None, "", "na", "-", "..."):
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        if -10.0 <= val <= 30.0:
            obs.append({"date": f"{y:04d}-{mth:02d}-01", "value": round(val, 2)})
    if not obs:
        print("    [diag] SingStat: no YoY values parsed from All Items row")
        return []
    obs.sort(key=lambda o: o["date"])
    print(f"  ✅ SingStat CPI All-Items YoY: {len(obs)} pts, latest {obs[-1]}")
    return obs


def fetch_nbs_cpi_series() -> List[Dict]:
    """China headline CPI (YoY %) from the NBS English press release (#56).

    NBS publishes monthly CPI press releases as HTML under
    /english/PressRelease/ with unpredictable numeric IDs, so we discover the
    latest CPI releases from the listing pages rather than guessing a URL. Each
    release carries a headline summary table whose first data row is

        Consumer Price Index   <M/M %>   <Y/Y %>   <Jan-N cumulative Y/Y %>

    e.g. "Consumer Price Index 0.3 1.2 0.9" for April 2026. We anchor on that
    row and take the second number (the monthly year-on-year rate); the month
    and year come from the release title "Consumer Price Index in <Month>
    <Year>". Falls back to FRED on any failure (returns []).
    """
    import re as _re
    headers = {"User-Agent": _BROWSER_UA,
               "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
               "Accept-Language": "en-US,en;q=0.9"}
    # The press-release index is dominated by high-frequency price-monitoring
    # bulletins, so the monthly CPI release is often a page or two back. Scan a
    # few index pages and match the specific "Consumer Price Index in <Month>"
    # title (not the broad "prices").
    base = "https://www.stats.gov.cn/english/PressRelease/"
    pages = [base, base + "index_1.html", base + "index_2.html", base + "index_3.html"]
    links = []
    for pg in pages:
        try:
            r = requests.get(pg, headers=headers, timeout=30)
            if r.status_code == 200:
                links += _re.findall(r'href="([^"]+\.html)"[^>]*>([^<]{0,140})', r.text)
        except Exception as e:
            print(f"[diag] NBS listing {pg} -> {type(e).__name__}", end="  ")
    # Keep the monthly "Consumer Price Index in <Month> <Year>" releases only.
    months = {name.lower(): i for i, name in enumerate(_MONTH_NAMES) if name}
    title_re = _re.compile(r"Consumer Price Index in (\w+)\s+(\d{4})", _re.I)
    seen = set()
    cpi_links = []
    for href, text in links:
        m = title_re.search(text)
        if not m:
            continue
        mi = months.get(m.group(1).lower())
        if not mi:
            continue
        key = (int(m.group(2)), mi)
        if key in seen:
            continue
        seen.add(key)
        cpi_links.append((href, key))
    if not cpi_links:
        print("[diag] NBS: no 'Consumer Price Index in <Month> <Year>' release on listings")
        return []
    # Newest first; parse a few recent releases so latest/previous are populated.
    cpi_links.sort(key=lambda x: x[1], reverse=True)

    row_re = _re.compile(
        r"Consumer Price Index\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)")
    obs = []
    for href, (yr, mi) in cpi_links[:3]:
        if href.startswith("http"):
            detail = href
        elif href.startswith("/"):
            detail = "https://www.stats.gov.cn" + href
        else:
            detail = base + href.lstrip("./")
        try:
            d = requests.get(detail, headers=headers, timeout=30)
            if d.status_code != 200:
                print(f"[diag] NBS detail {detail} -> {d.status_code}", end="  ")
                continue
        except Exception as e:
            print(f"[diag] NBS detail unreachable: {type(e).__name__}", end="  ")
            continue
        dtext = _re.sub(r"<[^>]+>", " ", d.text)
        dtext = _re.sub(r"\s+", " ", dtext)
        rm = row_re.search(dtext)
        if not rm:
            print(f"[diag] NBS {yr}-{mi:02d}: headline CPI row not found", end="  ")
            continue
        yoy = float(rm.group(2))  # M/M, Y/Y, cumulative Y/Y -> take Y/Y
        if -5.0 <= yoy <= 30.0:
            obs.append({"date": f"{yr:04d}-{mi:02d}-01", "value": round(yoy, 2)})

    if not obs:
        print("  ⏸️  NBS: no headline CPI parsed; preserving curated CN")
        return []
    obs.sort(key=lambda o: o["date"])
    print(f"  ✅ NBS headline CPI: {obs}")
    return obs


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

    # Tracks the source that actually produced the data, for per-record
    # provenance (#83): national fetchers can fall back to FRED, and the
    # NZ/KR rows are FRED-primary even though config["source"] names the
    # national agency.
    via_fred = False
    # The FRED series that actually produced the data (primary by default;
    # the FRED-primary path below may switch to fred_series_alt).
    fred_series_used = config.get("fred_series")

    try:
        if config.get("api") == "ECB":
            raw_data = fetch_ecb_series(config["series_id"])
            yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                       for obs in raw_data]
            # The ECB ICP series only carries the final print, so the EA row lags
            # one release. Append Eurostat's HICP flash when it's newer, flagged
            # provisional so the dashboard can mark it a flash estimate. #60
            try:
                # Union already-stored finals the ECB pull didn't return (keeps a
                # correct `previous` under the flash if the ECB feed is behind).
                have = {p["date"] for p in yoy_data}
                for p in (load_existing_data().get("EA", {}) or {}).get("history", []):
                    if p.get("date") not in have and isinstance(p.get("value"), (int, float)) \
                            and not p.get("provisional"):
                        entry = {"date": p["date"], "value": p["value"]}
                        for k in ("source", "source_url", "fetch_date"):
                            if k in p:
                                entry[k] = p[k]
                        if "source" not in entry:
                            # Reused stored final from before provenance was
                            # recorded — mark it so an --overwrite run can't
                            # stamp it as fetched today (#83).
                            entry["source"] = "ECB (stored final)"
                            entry["fetch_date"] = None
                        yoy_data.append(entry)
                yoy_data.sort(key=lambda x: x["date"])
                flash = fetch_eurostat_flash_release()
                latest_final = yoy_data[-1]["date"] if yoy_data else ""
                for fobs in flash:
                    fm = fobs["date"][:7]
                    if fm > latest_final:
                        yoy_data.append({"date": fm, "value": round(fobs["value"], 2),
                                         "provisional": True})
                yoy_data.sort(key=lambda x: x["date"])
            except Exception as e:
                print(f"(Eurostat flash skipped: {type(e).__name__}: {e})", end=" ")
        elif config.get("api") == "BLS":
            # Direct BLS Public Data API — no FRED lag.
            try:
                raw_data = fetch_bls_series(config["series_id"])
                if not raw_data:
                    raise ValueError(f"No data returned from BLS for {config['series_id']}")
                yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(BLS failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        elif config.get("api") == "ONS":
            # Direct ONS Beta API — series d7g7 is the headline CPI YoY.
            try:
                raw_data = fetch_ons_series(config["series_id"])
                if not raw_data:
                    raise ValueError(f"No data returned from ONS for {config['series_id']}")
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                           for obs in raw_data]
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(ONS failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        elif config.get("api") == "NBS":
            # Direct NBS English CPI press release (HTML) — already YoY. #56
            try:
                raw_data = fetch_nbs_cpi_series()
                if not raw_data:
                    raise ValueError("No data returned from NBS press release")
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                           for obs in raw_data]
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(NBS failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        elif config.get("api") == "eStat":
            # Direct e-Stat getStatsData — national all-items CPI, already YoY. #51
            try:
                raw_data = fetch_estat_cpi_series(config)
                if not raw_data:
                    raise ValueError("No data returned from e-Stat API")
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                           for obs in raw_data]
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(e-Stat failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        elif config.get("api") == "MoSPI":
            # Direct MoSPI CPI press release (PDF) — already YoY. #57
            try:
                raw_data = fetch_mospi_cpi_series()
                if not raw_data:
                    raise ValueError("No data returned from MoSPI press release")
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                           for obs in raw_data]
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(MoSPI failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        elif config.get("api") == "StatsSA":
            # Direct Stats SA P0141 release (PDF) — already YoY. #53
            try:
                raw_data = fetch_statssa_cpi_series()
                if not raw_data:
                    raise ValueError("No data returned from Stats SA P0141")
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                           for obs in raw_data]
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(StatsSA failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        elif config.get("api") == "ABS":
            # Australia (#106/#109): the landing-page headline tracks the ABS
            # monthly CPI indicator; the underlying historical series stays
            # quarterly. BOTH come from ABS (the source of truth) — monthly
            # drives latest/previous (the headline), the quarterly series is the
            # chart history — and history_replace makes merge rebuild (not
            # append) the quarterly series, scrubbing any monthly points that
            # leaked in before. FRED's quarterly relay is a fallback only.
            monthly_yoy = None
            try:
                raw_data = fetch_abs_cpi_series()  # monthly, already YoY (#50)
                if not raw_data:
                    raise ValueError("No YoY rows returned from ABS Data API")
                monthly_yoy = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                               for obs in raw_data]
            except Exception as e:
                print(f"(ABS monthly failed: {e})...", end=" ")

            # Quarterly history: ABS quarterly (current) → FRED relay (fallback).
            quarterly_history = []
            history_source = None
            try:
                quarterly_history = fetch_abs_quarterly_yoy()  # native YYYY-Qn (#109)
                if not quarterly_history:
                    raise ValueError("No quarterly YoY rows from ABS")
                history_source = "ABS"
            except Exception as e:
                print(f"(ABS quarterly failed: {e}; trying FRED)...", end=" ")
                if config.get("fred_series"):
                    try:
                        quarterly_history = calculate_yoy_from_index(
                            fetch_fred_series(config["fred_series"]), "quarterly")
                        history_source = "FRED" if quarterly_history else None
                    except Exception as e2:
                        print(f"(FRED quarterly history failed: {e2})...", end=" ")

            if not monthly_yoy and not quarterly_history:
                raise ValueError("Both ABS and FRED quarterly failed for AU")

            # latest/previous come from ABS monthly. If ABS is down we return
            # latest=None so merge KEEPS the existing monthly headline rather
            # than overwriting it with a coarser/older quarterly point (a
            # "YYYY-Qn" string sorts after "YYYY-MM", so the merge date guard
            # would otherwise treat an older quarter as newer).
            latest = monthly_yoy[-1] if monthly_yoy else None
            previous = (monthly_yoy[-2] if monthly_yoy and len(monthly_yoy) > 1
                        else None)
            print(f"✅ ABS monthly latest "
                  f"{latest['date'] if latest else 'n/a (ABS down)'}, "
                  f"{len(quarterly_history)} quarterly history pts "
                  f"({history_source or 'none'})")
            return {
                # Quarterly history drives the chart. When BOTH quarterly sources
                # are down we return an EMPTY history (NOT the monthly series):
                # with history_replace False, merge appends nothing and the
                # existing quarterly history is preserved — never polluted with
                # monthly points (the leak this change exists to scrub).
                "history": quarterly_history,
                "latest": latest,
                "previous": previous,
                "fetched_from": config["source"] if monthly_yoy else (history_source or "FRED"),
                "fred_series_used": config.get("fred_series"),
                # Rebuild the quarterly history wholesale only when we have it.
                "history_replace": bool(quarterly_history),
                "history_source": history_source,
            }
        elif config.get("api") == "SingStat":
            # Direct SingStat TableBuilder — monthly CPI All-Items, already YoY. #52
            try:
                raw_data = fetch_singstat_cpi_series(config)
                if not raw_data:
                    raise ValueError("No data returned from SingStat TableBuilder")
                yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                           for obs in raw_data]
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(SingStat failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    # The SG fallback is a World Bank annual YoY series (already a
                    # rate), not an index — don't run the YoY calc on it.
                    if config["fred_series"].startswith("FPCPITOTLZG"):
                        yoy_data = [{"date": obs["date"][:7], "value": round(obs["value"], 2)}
                                   for obs in raw_data]
                    else:
                        yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        elif config.get("api") == "StatCan":
            # Direct Statistics Canada Web Data Service — index, compute YoY.
            try:
                raw_data = fetch_statcan_series(config["series_id"])
                if not raw_data:
                    raise ValueError(f"No data returned from StatCan for vector {config['series_id']}")
                yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
            except Exception as e:
                if config.get("fred_series"):
                    print(f"(StatCan failed: {e}; falling back to FRED)...", end=" ")
                    via_fred = True
                    raw_data = fetch_fred_series(config["fred_series"])
                    yoy_data = calculate_yoy_from_index(raw_data, config.get("frequency", "monthly"))
                else:
                    raise
        else:
            # FRED API - try primary series, fall back to alt if available
            via_fred = True
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
                    fred_series_used = series_id
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
                "previous": yoy_data[-2] if len(yoy_data) > 1 else None,
                "fetched_from": "FRED" if via_fred else config["source"],
                "fred_series_used": fred_series_used if via_fred else None,
            }
        else:
            print("⚠️ No data")
            return None
            
    except Exception as e:
        print(f"❌ {e}")
        return None


US_SUPPLEMENTARY_SERIES = {
    "core_cpi": {"name": "Core CPI (ex Food & Energy)", "fred_series": "CPILFESL"},
    "pce": {"name": "PCE Price Index", "fred_series": "PCEPI"},
    "core_pce": {"name": "Core PCE", "fred_series": "PCEPILFE"},
}


def fetch_us_supplementary(existing: Optional[Dict]) -> Optional[Dict]:
    """Refresh the US supplementary metrics (Core CPI / PCE / Core PCE) from
    FRED as YoY rates (units=pc1).

    #99: these were hand-entered once (2026-03-24) and then frozen — nothing
    updated them. Now refreshed on every US merge, stamped with per-record
    provenance (#83). If FRED is unavailable the existing values are kept
    unchanged so they stay *visibly* stale (the freshness pill ages) rather
    than being silently fabricated or dropped.
    """
    if not FRED_API_KEY:
        print("    (supplementary skipped: FRED_API_KEY not set)")
        return existing
    fetch_stamp = datetime.now().strftime("%Y-%m-%d")
    out = {}
    for key, meta in US_SUPPLEMENTARY_SERIES.items():
        sid = meta["fred_series"]
        try:
            resp = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": sid, "api_key": FRED_API_KEY,
                    "file_type": "json", "sort_order": "desc",
                    "limit": 1, "units": "pc1",
                },
                timeout=30,
            )
            resp.raise_for_status()
            obs = [o for o in resp.json().get("observations", [])
                   if o.get("value") not in (None, ".")]
            if not obs:
                raise ValueError("no observations returned")
            out[key] = {
                "name": meta["name"],
                "latest": {
                    "date": obs[0]["date"][:7],
                    "value": round(float(obs[0]["value"]), 2),
                },
                "fred_series": sid,
                "source": "FRED",
                "source_url": f"https://fred.stlouisfed.org/series/{sid}",
                "fetch_date": fetch_stamp,
            }
        except Exception as e:
            print(f"    (supplementary {sid} failed: {e}; keeping existing)")
            if existing and key in existing:
                out[key] = existing[key]
    return out or existing


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
            "target": get_target(code),
            "source": config["source"],
            "source_url": config.get("source_url", ""),
            "fred_series": config.get("fred_series", ""),
            "frequency": config["frequency"],
            "history": []
        }

    # Config is the single source of truth for descriptive/provenance fields.
    # Refresh them on every merge so that migrating a country to a national
    # source (e.g. NBS direct instead of the OECD/FRED relay) updates the
    # displayed source label AND keeps source_url on the record (CLAUDE.md #3),
    # rather than leaving the stale value the existing JSON happened to carry.
    merged["name"] = config["name"]
    merged["flag"] = config["flag"]
    merged["target"] = get_target(code)
    merged["source"] = config["source"]
    merged["source_url"] = config.get("source_url", "")
    merged["fred_series"] = config.get("fred_series", "")

    # Preserve notes if they exist
    if config.get("notes") and "notes" not in merged:
        merged["notes"] = config["notes"]

    # US carries supplementary metrics (Core CPI / PCE / Core PCE) — refresh
    # them from FRED on every merge (#99); runs even when the headline fetch
    # failed so the cards don't freeze while the main series keeps moving.
    if code == "US":
        merged["supplementary"] = fetch_us_supplementary(merged.get("supplementary"))

    if not fetched:
        return merged
    
    # Get existing dates for quick lookup
    existing_dates = {h["date"] for h in merged.get("history", [])}
    existing_latest_date = max(existing_dates) if existing_dates else ""

    # Per-record provenance (CLAUDE.md #3, #83): histories are now
    # mixed-source (FRED/OECD backfill + direct-agency fetchers), so each
    # point we append records which source produced it and when we got it.
    # Pre-existing points are left untouched — we don't fabricate
    # provenance for data fetched before this was recorded.
    fetch_stamp = datetime.now().strftime("%Y-%m-%d")
    actual_source = fetched.get("fetched_from") or config["source"]
    fred_series_used = fetched.get("fred_series_used") or config.get("fred_series")
    actual_source_url = (
        f"https://fred.stlouisfed.org/series/{fred_series_used}"
        if actual_source == "FRED" and fred_series_used
        else config.get("source_url", "")
    )

    # Add new history points from the source
    new_points = 0
    if fetched.get("history_replace"):
        # AU (#106): the quarterly history is rebuilt wholesale from its
        # authoritative source each run, scrubbing any points appended under a
        # different cadence (e.g. monthly headline values that leaked in before
        # this split). Stamp per-point provenance; skip anomaly detection — a
        # full authoritative archive, like a backfill, isn't an "anomaly".
        hist_source = fetched.get("history_source") or actual_source
        hist_url = (
            f"https://fred.stlouisfed.org/series/{fred_series_used}"
            if hist_source == "FRED" and fred_series_used
            else config.get("source_url", "")
        )
        rebuilt = []
        for point in sorted(fetched.get("history", []), key=lambda x: x["date"]):
            point.setdefault("source", hist_source)
            point.setdefault("source_url", hist_url)
            point.setdefault("fetch_date", fetch_stamp)
            rebuilt.append(point)
        merged["history"] = rebuilt
        new_points = len(rebuilt)
    else:
        for point in fetched.get("history", []):
            if point["date"] not in existing_dates:
                # Only run anomaly detection on points newer than what we already
                # have. Backfill points (e.g. StatCan returning 20yrs of CA when
                # local history starts at 2016) come from the source's own
                # authoritative archive — flagging real historical volatility as
                # an "anomaly" just adds noise and trips CI.
                if point["date"] > existing_latest_date:
                    hist_so_far = sorted(merged.get("history", []), key=lambda x: x["date"])
                    prior = [h for h in hist_so_far if h["date"] < point["date"]]
                    prev = prior[-1] if prior else None
                    detect_anomalies(code, point, prev, hist_so_far)
                point.setdefault("source", actual_source)
                point.setdefault("source_url", actual_source_url)
                point.setdefault("fetch_date", fetch_stamp)
                merged.setdefault("history", []).append(point)
                new_points += 1

    # Sort history by date
    merged["history"] = sorted(merged.get("history", []), key=lambda x: x["date"])
    
    # Update latest/previous only if FRED has newer data
    if fetched.get("latest"):
        fred_latest_date = fetched["latest"]["date"]
        existing_latest_date = merged.get("latest", {}).get("date", "")
        
        if fred_latest_date > existing_latest_date:
            # Source has newer data
            fetched["latest"].setdefault("source", actual_source)
            fetched["latest"].setdefault("source_url", actual_source_url)
            fetched["latest"].setdefault("fetch_date", fetch_stamp)
            # Promote the outgoing latest to previous when the dates match —
            # it carries provenance the freshly-fetched previous dict lacks
            # (that date was already in history, so the append loop above
            # never stamped it).
            old_latest = merged.get("latest")
            new_prev = fetched.get("previous")
            if old_latest and new_prev and old_latest.get("date") == new_prev.get("date"):
                new_prev = old_latest
            merged["latest"] = fetched["latest"]
            merged["previous"] = new_prev or merged.get("previous")
            print(f"    → Updated latest: {fred_latest_date}")
        elif fred_latest_date == existing_latest_date:
            # Same reference period re-confirmed from source (#111). Refresh the
            # headline's value and provenance so it always carries source/url/
            # fetch_date (CLAUDE.md #3) even when the period hasn't advanced —
            # otherwise a record whose latest sits unchanged between prints
            # (e.g. AU's monthly headline) keeps a provenance-less value.
            # Existing extra fields (e.g. provisional) are preserved.
            refreshed = dict(merged.get("latest") or {})
            refreshed["value"] = fetched["latest"].get("value", refreshed.get("value"))
            refreshed["source"] = actual_source
            refreshed["source_url"] = actual_source_url
            refreshed["fetch_date"] = fetch_stamp
            merged["latest"] = refreshed
            print(f"    → Refreshed latest provenance: {fred_latest_date}")
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
