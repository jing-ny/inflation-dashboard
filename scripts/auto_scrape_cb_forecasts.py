#!/usr/bin/env python3
"""
Auto-Scrape Central Bank Forecasts
===================================

Automatically detects new central bank publications and extracts inflation forecasts.
Designed to run weekly via GitHub Actions.

Supports:
- RBA (Australia) - Statement on Monetary Policy
- ECB (Euro Area) - Staff Macroeconomic Projections  
- BoE (UK) - Monetary Policy Report
- BoC (Canada) - Monetary Policy Report
- RBNZ (New Zealand) - Monetary Policy Statement
- SARB (South Africa) - Monetary Policy Statement
- Fed (US) - FOMC SEP (via FRED API)

Usage:
    python auto_scrape_cb_forecasts.py              # Check all sources
    python auto_scrape_cb_forecasts.py --dry-run    # Check only, don't update
    python auto_scrape_cb_forecasts.py --country AU # Check specific country
    python auto_scrape_cb_forecasts.py --force      # Force update even if no new publication
"""

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURATION
# ============================================================

# File paths
STATE_FILE = Path("data/scraper_state.json")
OUTPUT_FILE = Path("data/cb_forecasts.json")
DOCS_OUTPUT = Path("docs/data/cb_forecasts.json")

# HTTP settings
HEADERS = {
    "User-Agent": "InflationDashboard/2.0 (https://github.com/jing-ny/inflation-dashboard)"
}
TIMEOUT = 30

# Publication schedules (for reference)
# RBA: Feb, May, Aug, Nov (quarterly)
# ECB: Mar, Jun, Sep, Dec (quarterly)
# BoE: Feb, May, Aug, Nov (quarterly)
# BoC: Jan, Apr, Jul, Oct (quarterly)
# RBNZ: Feb, May, Aug, Nov (quarterly)
# SARB: Jan, Mar, May, Jul, Sep, Nov (bi-monthly)
# Fed: Mar, Jun, Sep, Dec (quarterly)


@dataclass
class CentralBankSource:
    """Configuration for a central bank forecast source."""
    code: str
    name: str
    full_name: str
    index_url: str  # URL to check for new publications
    publication_pattern: str  # Regex to find publication links/dates
    forecast_url_template: Optional[str] = None  # Template for forecast page URL
    extractor: str = "generic"  # Which extractor function to use
    target: float = 2.0
    target_range: Optional[Tuple[float, float]] = None
    measure: str = "CPI"
    notes: str = ""


# Central bank source configurations
SOURCES: Dict[str, CentralBankSource] = {
    "AU": CentralBankSource(
        code="AU",
        name="RBA",
        full_name="Reserve Bank of Australia",
        index_url="https://www.rba.gov.au/publications/smp/",
        publication_pattern=r"/publications/smp/(\d{4})/(feb|may|aug|nov)/",
        forecast_url_template="https://www.rba.gov.au/publications/smp/{year}/{month}/outlook.html",
        extractor="rba",
        target=2.5,
        target_range=(2.0, 3.0),
        measure="Trimmed Mean CPI",
        notes="Trimmed mean inflation, quarterly publication"
    ),
    "EA": CentralBankSource(
        code="EA",
        name="ECB",
        full_name="European Central Bank",
        index_url="https://www.ecb.europa.eu/press/projections/html/index.en.html",
        publication_pattern=r"projections(\d{6})_eurosystemstaff",
        forecast_url_template="https://www.ecb.europa.eu/press/projections/html/ecb.projections{date}_eurosystemstaff~{hash}.en.html",
        extractor="ecb",
        target=2.0,
        measure="HICP",
        notes="Staff macroeconomic projections, quarterly"
    ),
    "UK": CentralBankSource(
        code="UK",
        name="BoE",
        full_name="Bank of England",
        index_url="https://www.bankofengland.co.uk/monetary-policy-report",
        publication_pattern=r"/monetary-policy-report/(\d{4})/(february|may|august|november)-\d{4}",
        extractor="boe",
        target=2.0,
        measure="CPI",
        notes="Modal CPI projections from MPR"
    ),
    "CA": CentralBankSource(
        code="CA",
        name="BoC",
        full_name="Bank of Canada",
        index_url="https://www.bankofcanada.ca/publications/mpr/",
        publication_pattern=r"/mpr/mpr-(\d{4})-(\d{2})-(\d{2})/",
        extractor="boc",
        target=2.0,
        target_range=(1.0, 3.0),
        measure="CPI",
        notes="Inflation expected to remain around 2%"
    ),
    "NZ": CentralBankSource(
        code="NZ",
        name="RBNZ",
        full_name="Reserve Bank of New Zealand",
        index_url="https://www.rbnz.govt.nz/hub/publications/monetary-policy-statement",
        publication_pattern=r"/monetary-policy-statement/(\d{4})/(feb|may|aug|nov)",
        extractor="rbnz",
        target=2.0,
        target_range=(1.0, 3.0),
        measure="CPI",
        notes="Target midpoint 2%, range 1-3%"
    ),
    "ZA": CentralBankSource(
        code="ZA",
        name="SARB",
        full_name="South African Reserve Bank",
        index_url="https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements",
        publication_pattern=r"monetary-policy-statements/(\d{4})",
        extractor="sarb",
        target=4.5,
        target_range=(3.0, 6.0),
        measure="CPI",
        notes="Target range 3-6%, midpoint 4.5%"
    ),
}

# Fallback manual forecasts (used if scraping fails)
MANUAL_FORECASTS = {
    "US": {
        "source": "FOMC Summary of Economic Projections",
        "source_url": "https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20251218.htm",
        "last_updated": "December 2025",
        "measure": "PCE inflation (median projection)",
        "forecasts": [
            {"year": 2025, "value": 2.8},
            {"year": 2026, "value": 2.4},
            {"year": 2027, "value": 2.1},
        ]
    },
    "EA": {
        "source": "ECB Staff Macroeconomic Projections",
        "source_url": "https://www.ecb.europa.eu/press/projections/html/index.en.html",
        "last_updated": "December 2025",
        "measure": "HICP inflation",
        "forecasts": [
            {"year": 2025, "value": 2.1},
            {"year": 2026, "value": 1.9},
            {"year": 2027, "value": 1.8},
            {"year": 2028, "value": 2.0},
        ]
    },
    "UK": {
        "source": "Bank of England Monetary Policy Report",
        "source_url": "https://www.bankofengland.co.uk/monetary-policy-report/2025/november-2025",
        "last_updated": "November 2025",
        "measure": "CPI inflation (modal projection)",
        "forecasts": [
            {"year": 2025, "value": 3.5},
            {"year": 2026, "value": 2.5},
            {"year": 2027, "value": 2.0},
        ]
    },
    "AU": {
        "source": "RBA Statement on Monetary Policy",
        "source_url": "https://www.rba.gov.au/publications/smp/2025/nov/outlook.html",
        "last_updated": "November 2025",
        "measure": "Trimmed mean inflation",
        "forecasts": [
            {"year": 2025, "value": 3.2},
            {"year": 2026, "value": 2.7},
            {"year": 2027, "value": 2.6},
        ]
    },
    "CA": {
        "source": "Bank of Canada Monetary Policy Report",
        "source_url": "https://www.bankofcanada.ca/publications/mpr/mpr-2025-10-29/",
        "last_updated": "October 2025",
        "measure": "CPI inflation",
        "forecasts": [
            {"year": 2025, "value": 2.4},
            {"year": 2026, "value": 2.0},
            {"year": 2027, "value": 2.0},
        ]
    },
    "NZ": {
        "source": "RBNZ Monetary Policy Statement",
        "source_url": "https://www.rbnz.govt.nz/hub/publications/monetary-policy-statement/2025/nov-1125/",
        "last_updated": "November 2025",
        "measure": "CPI inflation",
        "forecasts": [
            {"year": 2025, "value": 3.0},
            {"year": 2026, "value": 2.0},
            {"year": 2027, "value": 2.0},
        ]
    },
    "ZA": {
        "source": "SARB Monetary Policy Statement",
        "source_url": "https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements",
        "last_updated": "November 2025",
        "measure": "CPI inflation",
        "forecasts": [
            {"year": 2025, "value": 3.3},
            {"year": 2026, "value": 3.5},
            {"year": 2027, "value": 3.1},
        ]
    },
    "CN": {
        "source": "IMF World Economic Outlook",
        "source_url": "https://www.imf.org/en/Publications/WEO",
        "last_updated": "October 2025",
        "measure": "CPI inflation (IMF projection)",
        "forecasts": [
            {"year": 2025, "value": 0.5},
            {"year": 2026, "value": 1.2},
        ]
    },
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def fetch_page(url: str, timeout: int = TIMEOUT) -> Optional[str]:
    """Fetch a web page and return its HTML content."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"    ⚠️ Error fetching {url}: {e}")
        return None


def get_content_hash(html: str) -> str:
    """Generate a hash of page content (excluding dynamic elements)."""
    # Remove scripts, styles, and common dynamic content
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)
    clean = re.sub(r'\s+', ' ', clean)
    return hashlib.md5(clean.encode()).hexdigest()[:16]


def load_state() -> Dict:
    """Load scraper state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: Dict):
    """Save scraper state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_existing_forecasts() -> Dict:
    """Load existing cb_forecasts.json if it exists."""
    if OUTPUT_FILE.exists():
        try:
            return json.loads(OUTPUT_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"generated_at": "", "forecasts": {}}


def save_forecasts(data: Dict):
    """Save forecasts to both data/ and docs/data/."""
    data["generated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Save to data/
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(data, indent=2))
    
    # Save to docs/data/
    DOCS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOCS_OUTPUT.write_text(json.dumps(data, indent=2))
    
    print(f"\n✅ Saved forecasts to {OUTPUT_FILE} and {DOCS_OUTPUT}")


# ============================================================
# PUBLICATION DETECTION
# ============================================================

def detect_new_publication(source: CentralBankSource, state: Dict) -> Optional[Dict]:
    """
    Check if there's a new publication for a central bank.
    Returns publication info if new, None otherwise.
    """
    print(f"\n🔍 Checking {source.code} ({source.name})...")
    
    html = fetch_page(source.index_url)
    if not html:
        return None
    
    # Check content hash for changes
    current_hash = get_content_hash(html)
    prev_hash = state.get(source.code, {}).get("hash")
    
    if current_hash == prev_hash:
        print(f"    📋 No changes detected")
        return None
    
    # Find latest publication
    matches = re.findall(source.publication_pattern, html, re.IGNORECASE)
    if not matches:
        print(f"    ⚠️ No publications found matching pattern")
        return None
    
    # Get the most recent match
    latest = matches[0] if isinstance(matches[0], str) else "/".join(matches[0])
    prev_pub = state.get(source.code, {}).get("publication")
    
    if latest == prev_pub:
        print(f"    📋 Same publication as before: {latest}")
        # Update hash anyway
        return {"hash": current_hash, "publication": latest, "is_new": False}
    
    print(f"    🆕 New publication detected: {latest}")
    return {"hash": current_hash, "publication": latest, "is_new": True}


# ============================================================
# FORECAST EXTRACTORS
# ============================================================

def extract_rba_forecasts(html: str, source: CentralBankSource) -> Optional[Dict]:
    """
    Extract inflation forecasts from RBA Statement on Monetary Policy.
    Looks for Table 3.1 with detailed forecasts.
    """
    soup = BeautifulSoup(html, 'html.parser')
    forecasts = []
    
    # Look for forecast table (Table 3.1)
    # RBA uses tables with specific headers
    tables = soup.find_all('table')
    
    for table in tables:
        text = table.get_text().lower()
        
        # Look for trimmed mean or CPI inflation rows
        if 'trimmed mean' in text or 'underlying inflation' in text:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = [c.get_text().strip() for c in row.find_all(['td', 'th'])]
                row_text = ' '.join(cells).lower()
                
                # Look for inflation forecast row
                if 'trimmed mean' in row_text or 'inflation' in row_text:
                    # Extract year/quarter and value pairs
                    for i, cell in enumerate(cells):
                        # Look for year patterns
                        year_match = re.search(r'(202[5-9]|203[0-9])', cell)
                        if year_match and i + 1 < len(cells):
                            try:
                                value = float(re.search(r'(\d+\.?\d*)', cells[i+1]).group(1))
                                forecasts.append({
                                    "year": int(year_match.group(1)),
                                    "value": value
                                })
                            except (ValueError, AttributeError):
                                continue
    
    # Also try to extract from prose text
    if not forecasts:
        text = soup.get_text()
        # Pattern: "underlying inflation is expected to be X% in YYYY"
        pattern = r'(?:inflation|trimmed mean)[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)[^.]*?(?:in|by)\s*(202[5-9]|203[0-9])'
        matches = re.findall(pattern, text, re.IGNORECASE)
        for value, year in matches:
            forecasts.append({"year": int(year), "value": float(value)})
    
    if forecasts:
        # Deduplicate and sort by year
        seen = set()
        unique_forecasts = []
        for f in forecasts:
            key = f["year"]
            if key not in seen:
                seen.add(key)
                unique_forecasts.append(f)
        unique_forecasts.sort(key=lambda x: x["year"])
        
        return {
            "source": source.full_name,
            "source_url": source.index_url,
            "last_updated": datetime.now().strftime("%B %Y"),
            "measure": source.measure,
            "forecasts": unique_forecasts[:4]  # Limit to 4 years
        }
    
    return None


def extract_ecb_forecasts(html: str, source: CentralBankSource) -> Optional[Dict]:
    """
    Extract inflation forecasts from ECB staff projections page.
    """
    soup = BeautifulSoup(html, 'html.parser')
    forecasts = []
    
    # ECB typically has projections in a table or structured text
    text = soup.get_text()
    
    # Pattern: "HICP inflation averaging X% in YYYY"
    # or "headline inflation is expected to be X.X% in YYYY"
    patterns = [
        r'(?:HICP|headline)\s*inflation[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)[^.]*?(?:in|for)\s*(202[5-9]|203[0-9])',
        r'(202[5-9]|203[0-9])[^,]*?(?:HICP|inflation)[^,]*?(\d+\.?\d*)\s*(?:per\s*cent|%)',
        r'averaging\s*(\d+\.?\d*)\s*(?:per\s*cent|%)\s*in\s*(202[5-9]|203[0-9])',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if match[0].startswith('20'):  # Year first
                    year, value = int(match[0]), float(match[1])
                else:
                    value, year = float(match[0]), int(match[1])
                forecasts.append({"year": year, "value": value})
            except (ValueError, IndexError):
                continue
    
    # Also check for the standard ECB projection format
    # "2025: 2.1%, 2026: 1.9%, 2027: 1.8%"
    year_value_pattern = r'(202[5-9])\s*[:\-]?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)?'
    matches = re.findall(year_value_pattern, text)
    for year, value in matches:
        try:
            forecasts.append({"year": int(year), "value": float(value)})
        except ValueError:
            continue
    
    if forecasts:
        # Deduplicate
        seen = set()
        unique = []
        for f in forecasts:
            if f["year"] not in seen and 1.0 <= f["value"] <= 10.0:  # Sanity check
                seen.add(f["year"])
                unique.append(f)
        unique.sort(key=lambda x: x["year"])
        
        return {
            "source": source.full_name,
            "source_url": source.index_url,
            "last_updated": datetime.now().strftime("%B %Y"),
            "measure": source.measure,
            "forecasts": unique[:4]
        }
    
    return None


def extract_boe_forecasts(html: str, source: CentralBankSource) -> Optional[Dict]:
    """
    Extract inflation forecasts from Bank of England Monetary Policy Report.
    """
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    forecasts = []
    
    # BoE uses patterns like:
    # "CPI inflation is projected to fall to X% by YYYY"
    # "inflation to be around X% in YYYY"
    patterns = [
        r'(?:CPI\s*)?inflation[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)[^.]*?(?:in|by|for)\s*(?:Q\d\s*)?(202[5-9]|203[0-9])',
        r'(202[5-9]|203[0-9])[^,]*?(?:CPI|inflation)[^,]*?(\d+\.?\d*)\s*(?:per\s*cent|%)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if match[0].startswith('20'):
                    year, value = int(match[0]), float(match[1])
                else:
                    value, year = float(match[0]), int(match[1])
                if 0 <= value <= 10:  # Sanity check
                    forecasts.append({"year": year, "value": value})
            except (ValueError, IndexError):
                continue
    
    if forecasts:
        seen = set()
        unique = []
        for f in forecasts:
            if f["year"] not in seen:
                seen.add(f["year"])
                unique.append(f)
        unique.sort(key=lambda x: x["year"])
        
        return {
            "source": source.full_name,
            "source_url": source.index_url,
            "last_updated": datetime.now().strftime("%B %Y"),
            "measure": source.measure,
            "forecasts": unique[:4]
        }
    
    return None


def extract_boc_forecasts(html: str, source: CentralBankSource) -> Optional[Dict]:
    """
    Extract inflation forecasts from Bank of Canada Monetary Policy Report.
    """
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    forecasts = []
    
    # BoC patterns
    patterns = [
        r'(?:CPI\s*)?inflation[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)[^.]*?(?:in|for|through)\s*(202[5-9]|203[0-9])',
        r'inflation\s*(?:is\s*)?(?:expected|projected)[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                value = float(match[0])
                year = int(match[1]) if len(match) > 1 else datetime.now().year
                if 0 <= value <= 10:
                    forecasts.append({"year": year, "value": value})
            except (ValueError, IndexError):
                continue
    
    if forecasts:
        seen = set()
        unique = []
        for f in forecasts:
            if f["year"] not in seen:
                seen.add(f["year"])
                unique.append(f)
        unique.sort(key=lambda x: x["year"])
        
        return {
            "source": source.full_name,
            "source_url": source.index_url,
            "last_updated": datetime.now().strftime("%B %Y"),
            "measure": source.measure,
            "forecasts": unique[:3]
        }
    
    return None


def extract_rbnz_forecasts(html: str, source: CentralBankSource) -> Optional[Dict]:
    """
    Extract inflation forecasts from RBNZ Monetary Policy Statement.
    """
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    forecasts = []
    
    # RBNZ patterns
    patterns = [
        r'inflation[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)[^.]*?(?:target|midpoint)',
        r'(?:CPI\s*)?inflation[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)[^.]*?(?:in|by)\s*(202[5-9]|203[0-9])',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if isinstance(match, tuple):
                    value = float(match[0])
                    year = int(match[1]) if len(match) > 1 else datetime.now().year + 1
                else:
                    value = float(match)
                    year = datetime.now().year + 1
                if 0 <= value <= 10:
                    forecasts.append({"year": year, "value": value})
            except (ValueError, IndexError):
                continue
    
    if forecasts:
        seen = set()
        unique = []
        for f in forecasts:
            if f["year"] not in seen:
                seen.add(f["year"])
                unique.append(f)
        unique.sort(key=lambda x: x["year"])
        
        return {
            "source": source.full_name,
            "source_url": source.index_url,
            "last_updated": datetime.now().strftime("%B %Y"),
            "measure": source.measure,
            "forecasts": unique[:3]
        }
    
    return None


def extract_sarb_forecasts(html: str, source: CentralBankSource) -> Optional[Dict]:
    """
    Extract inflation forecasts from SARB Monetary Policy Statement.
    """
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    forecasts = []
    
    # SARB patterns
    patterns = [
        r'(?:CPI\s*)?inflation[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)[^.]*?(?:in|for)\s*(202[5-9]|203[0-9])',
        r'forecast[^.]*?inflation[^.]*?(\d+\.?\d*)\s*(?:per\s*cent|%)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if isinstance(match, tuple):
                    value, year = float(match[0]), int(match[1])
                else:
                    value = float(match)
                    year = datetime.now().year
                if 0 <= value <= 15:  # SARB can have higher inflation
                    forecasts.append({"year": year, "value": value})
            except (ValueError, IndexError):
                continue
    
    if forecasts:
        seen = set()
        unique = []
        for f in forecasts:
            if f["year"] not in seen:
                seen.add(f["year"])
                unique.append(f)
        unique.sort(key=lambda x: x["year"])
        
        return {
            "source": source.full_name,
            "source_url": source.index_url,
            "last_updated": datetime.now().strftime("%B %Y"),
            "measure": source.measure,
            "forecasts": unique[:3]
        }
    
    return None


# Extractor function mapping
EXTRACTORS = {
    "rba": extract_rba_forecasts,
    "ecb": extract_ecb_forecasts,
    "boe": extract_boe_forecasts,
    "boc": extract_boc_forecasts,
    "rbnz": extract_rbnz_forecasts,
    "sarb": extract_sarb_forecasts,
}


def extract_forecasts(html: str, source: CentralBankSource) -> Optional[Dict]:
    """Extract forecasts using the appropriate extractor."""
    extractor = EXTRACTORS.get(source.extractor)
    if extractor:
        return extractor(html, source)
    return None


# ============================================================
# MAIN SCRAPING LOGIC
# ============================================================

def scrape_source(source: CentralBankSource, state: Dict, force: bool = False, dry_run: bool = False) -> Optional[Dict]:
    """
    Scrape a single central bank source.
    Returns forecast data if successful, None otherwise.
    """
    # Check for new publication
    pub_info = detect_new_publication(source, state)
    
    if not pub_info:
        print(f"    ⚠️ Could not check for updates")
        return None
    
    # Update state hash
    if not dry_run:
        state.setdefault(source.code, {})["hash"] = pub_info["hash"]
    
    if not pub_info.get("is_new") and not force:
        print(f"    ℹ️ No new publication, using cached data")
        return None
    
    # Fetch and parse forecast page
    if source.forecast_url_template and pub_info.get("publication"):
        # Build URL from template
        parts = pub_info["publication"].split("/")
        if len(parts) >= 2:
            forecast_url = source.forecast_url_template.format(
                year=parts[0], 
                month=parts[1].lower()
            )
        else:
            forecast_url = source.index_url
    else:
        forecast_url = source.index_url
    
    print(f"    📄 Fetching: {forecast_url}")
    html = fetch_page(forecast_url)
    
    if not html:
        print(f"    ⚠️ Could not fetch forecast page")
        return None
    
    # Extract forecasts
    forecasts = extract_forecasts(html, source)
    
    if forecasts:
        print(f"    ✅ Extracted {len(forecasts['forecasts'])} forecast(s)")
        
        # Update state
        if not dry_run:
            state[source.code]["publication"] = pub_info["publication"]
            state[source.code]["last_scraped"] = datetime.now().isoformat()
        
        return forecasts
    else:
        print(f"    ⚠️ Could not extract forecasts from page")
        return None


def run_scraper(
    countries: Optional[List[str]] = None,
    force: bool = False,
    dry_run: bool = False,
    use_manual_fallback: bool = True
) -> Dict:
    """
    Run the scraper for specified countries or all.
    Returns a dictionary of forecasts.
    """
    print("=" * 60)
    print("Central Bank Forecast Auto-Scraper")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)
    
    # Load state
    state = load_state()
    
    # Load existing forecasts
    existing = load_existing_forecasts()
    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecasts": existing.get("forecasts", {})
    }
    
    # Determine which countries to process
    if countries:
        sources_to_check = {k: v for k, v in SOURCES.items() if k in countries}
    else:
        sources_to_check = SOURCES
    
    # Process each source
    updates = []
    for code, source in sources_to_check.items():
        try:
            forecasts = scrape_source(source, state, force, dry_run)
            
            if forecasts:
                result["forecasts"][code] = forecasts
                updates.append(code)
            elif use_manual_fallback and code in MANUAL_FORECASTS:
                # Use manual fallback if scraping failed
                if code not in result["forecasts"]:
                    print(f"    📋 Using manual fallback for {code}")
                    result["forecasts"][code] = MANUAL_FORECASTS[code]
        except Exception as e:
            print(f"    ❌ Error processing {code}: {e}")
            if use_manual_fallback and code in MANUAL_FORECASTS:
                result["forecasts"][code] = MANUAL_FORECASTS[code]
    
    # Add US and CN from manual (no web scraping for these)
    for code in ["US", "CN"]:
        if code not in result["forecasts"] and code in MANUAL_FORECASTS:
            result["forecasts"][code] = MANUAL_FORECASTS[code]
    
    # Save results
    if not dry_run:
        save_state(state)
        save_forecasts(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Sources checked: {len(sources_to_check)}")
    print(f"Updates found: {len(updates)}")
    if updates:
        print(f"Updated: {', '.join(updates)}")
    print(f"Total forecasts: {len(result['forecasts'])}")
    
    return result


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Auto-scrape central bank inflation forecasts"
    )
    parser.add_argument(
        "--country", "-c",
        nargs="+",
        choices=list(SOURCES.keys()) + ["US", "CN"],
        help="Specific country codes to check"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force update even if no new publication detected"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Check for updates but don't save anything"
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Don't use manual fallback if scraping fails"
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List all configured sources and exit"
    )
    
    args = parser.parse_args()
    
    if args.list_sources:
        print("\nConfigured Central Bank Sources:")
        print("-" * 60)
        for code, source in SOURCES.items():
            print(f"  {code}: {source.name} ({source.full_name})")
            print(f"       URL: {source.index_url}")
            print(f"       Measure: {source.measure}")
            print()
        print("Manual-only sources:")
        print(f"  US: Federal Reserve (FOMC SEP)")
        print(f"  CN: IMF World Economic Outlook")
        return
    
    # Install dependencies check
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install requests beautifulsoup4")
        sys.exit(1)
    
    # Run scraper
    countries = [c.upper() for c in args.country] if args.country else None
    
    result = run_scraper(
        countries=countries,
        force=args.force,
        dry_run=args.dry_run,
        use_manual_fallback=not args.no_fallback
    )
    
    # Exit code based on whether any updates were found
    if result.get("forecasts"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
