#!/usr/bin/env python3
"""
Auto-scrape Central Bank Forecasts

Fetches forecast pages from central banks, extracts inflation projections
using pattern matching, and outputs a draft JSON for review.

Usage:
    python scripts/auto_scrape_cb_forecasts.py

Output:
    - data/cb_forecasts_draft.json (new values found)
    - data/cb_forecasts_changes.md (summary of changes for PR)
"""

import json
import re
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
import ssl

# Disable SSL verification for some government sites
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

CURRENT_YEAR = datetime.now().year
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; InflationDashboard/1.0)'}


def fetch_url(url):
    """Fetch URL content with error handling."""
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30, context=ssl_context) as response:
            return response.read().decode('utf-8', errors='ignore')
    except URLError as e:
        print(f"  ❌ Failed to fetch {url}: {e}")
        return None


def extract_numbers(text, around_pattern, count=4):
    """Extract decimal numbers near a pattern."""
    # Find the pattern and get surrounding text
    match = re.search(around_pattern, text, re.IGNORECASE)
    if not match:
        return []
    
    # Get text around the match
    start = max(0, match.start() - 200)
    end = min(len(text), match.end() + 500)
    context = text[start:end]
    
    # Extract numbers that look like inflation rates (0.0 - 15.0)
    numbers = re.findall(r'(\d{1,2}\.\d{1})', context)
    # Filter to reasonable inflation values
    values = [float(n) for n in numbers if 0.0 <= float(n) <= 15.0]
    return values[:count]


def scrape_ecb():
    """Scrape ECB Staff Projections."""
    print("📊 Scraping ECB...")
    url = "https://www.ecb.europa.eu/pub/projections/html/ecb.projections202412_ecbstaff~14c709ec36.en.html"
    
    # Try to find the latest projections page
    index_url = "https://www.ecb.europa.eu/pub/projections/html/index.en.html"
    index_html = fetch_url(index_url)
    
    if index_html:
        # Find latest projection link
        links = re.findall(r'href="([^"]*projections\d{6}[^"]*\.en\.html)"', index_html)
        if links:
            url = "https://www.ecb.europa.eu" + links[0] if links[0].startswith('/') else links[0]
    
    html = fetch_url(url)
    if not html:
        return None
    
    # Look for HICP inflation table
    # ECB format: years in header, HICP row with values
    result = {
        "bank": "European Central Bank",
        "country": "EA",
        "metric": "HICP Inflation",
        "source": "ECB Staff Projections",
        "source_url": url,
        "projections": []
    }
    
    # Try to extract from table structure
    # Pattern: look for HICP followed by year values
    hicp_match = re.search(r'HICP[^<]*</t[dh]>[^<]*(?:<t[dh][^>]*>[^<]*(\d\.\d)[^<]*</t[dh]>[^<]*){2,4}', html, re.IGNORECASE | re.DOTALL)
    
    if hicp_match:
        values = re.findall(r'>(\d\.\d)<', hicp_match.group(0))
        years = [str(CURRENT_YEAR + i) for i in range(len(values))]
        result["projections"] = [{"year": y, "value": float(v)} for y, v in zip(years, values)]
    else:
        # Fallback: extract numbers near "HICP" or "inflation"
        values = extract_numbers(html, r'HICP.*?inflation|inflation.*?HICP', 4)
        if values:
            years = [str(CURRENT_YEAR + i) for i in range(len(values))]
            result["projections"] = [{"year": y, "value": v} for y, v in zip(years, values)]
    
    # Extract date from URL or page
    date_match = re.search(r'(\w+)\s+20\d{2}.*?projections', html, re.IGNORECASE)
    if date_match:
        result["source_date"] = date_match.group(0)[:20]
    
    return result if result["projections"] else None


def scrape_boe():
    """Scrape Bank of England Monetary Policy Report."""
    print("📊 Scraping BoE...")
    
    # BoE MPR page
    url = "https://www.bankofengland.co.uk/monetary-policy-report/2024/november-2024"
    
    # Try to find latest MPR
    index_url = "https://www.bankofengland.co.uk/monetary-policy-report"
    index_html = fetch_url(index_url)
    
    if index_html:
        links = re.findall(r'href="(/monetary-policy-report/\d{4}/[^"]+)"', index_html)
        if links:
            url = "https://www.bankofengland.co.uk" + links[0]
    
    html = fetch_url(url)
    if not html:
        return None
    
    result = {
        "bank": "Bank of England",
        "country": "UK",
        "metric": "CPI Inflation",
        "source": "Monetary Policy Report",
        "source_url": url,
        "projections": []
    }
    
    # BoE often shows projections in format like "2.5% in 2025"
    pattern = r'(\d\.\d)%?\s*(?:in|for)?\s*(202[4-9])'
    matches = re.findall(pattern, html)
    
    if matches:
        seen_years = set()
        for value, year in matches:
            if year not in seen_years and 0 < float(value) < 10:
                result["projections"].append({"year": year, "value": float(value)})
                seen_years.add(year)
    
    # Extract date from URL
    date_match = re.search(r'/(\w+-\d{4})/?$', url)
    if date_match:
        result["source_date"] = date_match.group(1).replace('-', ' ').title()
    
    return result if result["projections"] else None


def scrape_rba():
    """Scrape RBA Statement on Monetary Policy."""
    print("📊 Scraping RBA...")
    
    url = "https://www.rba.gov.au/publications/smp/2024/nov/economic-outlook.html"
    
    # Try to find latest SoMP
    index_url = "https://www.rba.gov.au/publications/smp/"
    index_html = fetch_url(index_url)
    
    if index_html:
        links = re.findall(r'href="(/publications/smp/\d{4}/\w+/)"', index_html)
        if links:
            url = "https://www.rba.gov.au" + links[0] + "economic-outlook.html"
    
    html = fetch_url(url)
    if not html:
        return None
    
    result = {
        "bank": "Reserve Bank of Australia",
        "country": "AU",
        "metric": "CPI Inflation",
        "source": "Statement on Monetary Policy",
        "source_url": url,
        "projections": []
    }
    
    # RBA shows forecasts in tables, look for CPI/inflation rows
    values = extract_numbers(html, r'trimmed.mean|underlying.*inflation|CPI', 4)
    
    if values:
        # RBA typically shows Jun and Dec for each year
        years = [str(CURRENT_YEAR), str(CURRENT_YEAR + 1), str(CURRENT_YEAR + 2)]
        result["projections"] = [{"year": y, "value": v} for y, v in zip(years, values[:3])]
    
    return result if result["projections"] else None


def scrape_boc():
    """Scrape Bank of Canada Monetary Policy Report."""
    print("📊 Scraping BoC...")
    
    url = "https://www.bankofcanada.ca/2024/10/mpr-2024-10-23/"
    
    # Try to find latest MPR
    index_url = "https://www.bankofcanada.ca/publications/mpr/"
    index_html = fetch_url(index_url)
    
    if index_html:
        links = re.findall(r'href="(https://www\.bankofcanada\.ca/\d{4}/\d{2}/mpr-[^"]+)"', index_html)
        if links:
            url = links[0]
    
    html = fetch_url(url)
    if not html:
        return None
    
    result = {
        "bank": "Bank of Canada",
        "country": "CA",
        "metric": "CPI Inflation",
        "source": "Monetary Policy Report",
        "source_url": url,
        "projections": []
    }
    
    # BoC format varies, look for projection tables
    values = extract_numbers(html, r'CPI.*inflation|inflation.*projection', 4)
    
    if values:
        years = [str(CURRENT_YEAR + i) for i in range(len(values))]
        result["projections"] = [{"year": y, "value": v} for y, v in zip(years, values)]
    
    return result if result["projections"] else None


def scrape_rbnz():
    """Scrape RBNZ Monetary Policy Statement."""
    print("📊 Scraping RBNZ...")
    
    url = "https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement/mps-november-2024"
    
    # Try to find latest MPS
    index_url = "https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement"
    index_html = fetch_url(index_url)
    
    if index_html:
        links = re.findall(r'href="(/monetary-policy/monetary-policy-statement/mps-[^"]+)"', index_html)
        if links:
            url = "https://www.rbnz.govt.nz" + links[0]
    
    html = fetch_url(url)
    if not html:
        return None
    
    result = {
        "bank": "Reserve Bank of New Zealand",
        "country": "NZ",
        "metric": "CPI Inflation",
        "source": "Monetary Policy Statement",
        "source_url": url,
        "projections": []
    }
    
    values = extract_numbers(html, r'CPI.*inflation|headline.*inflation', 4)
    
    if values:
        years = [str(CURRENT_YEAR + i) for i in range(len(values))]
        result["projections"] = [{"year": y, "value": v} for y, v in zip(years, values)]
    
    return result if result["projections"] else None


def scrape_sarb():
    """Scrape SARB MPC Statement."""
    print("📊 Scraping SARB...")
    
    # SARB publishes forecasts in MPC statements (PDFs), harder to scrape
    # Try the main monetary policy page for any HTML summaries
    url = "https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements/2024"
    
    html = fetch_url(url)
    if not html:
        return None
    
    result = {
        "bank": "South African Reserve Bank",
        "country": "ZA",
        "metric": "CPI Inflation",
        "source": "MPC Statement",
        "source_url": url,
        "projections": []
    }
    
    # SARB often mentions forecasts like "inflation is expected to average X% in 202Y"
    pattern = r'(?:inflation|CPI).*?(\d\.\d)%?\s*(?:in|for|by)?\s*(202[4-9])'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    if matches:
        seen_years = set()
        for value, year in matches:
            if year not in seen_years:
                result["projections"].append({"year": year, "value": float(value)})
                seen_years.add(year)
    
    return result if result["projections"] else None


def load_current_forecasts():
    """Load current cb_forecasts.json for comparison."""
    path = "docs/data/cb_forecasts.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"forecasts": []}


def compare_forecasts(current, new):
    """Compare current and new forecasts, return changes."""
    changes = []
    
    current_by_bank = {f["bank"]: f for f in current.get("forecasts", [])}
    
    for new_forecast in new:
        bank = new_forecast["bank"]
        if bank in current_by_bank:
            old = current_by_bank[bank]
            old_proj = {p["year"]: p["value"] for p in old.get("projections", [])}
            new_proj = {p["year"]: p["value"] for p in new_forecast.get("projections", [])}
            
            for year, value in new_proj.items():
                old_value = old_proj.get(year)
                if old_value != value:
                    changes.append({
                        "bank": bank,
                        "year": year,
                        "old": old_value,
                        "new": value
                    })
        else:
            changes.append({
                "bank": bank,
                "year": "all",
                "old": None,
                "new": new_forecast["projections"]
            })
    
    return changes


def main():
    print("🔄 Auto-scraping Central Bank Forecasts...")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # Scrape each bank
    scrapers = [
        scrape_ecb,
        scrape_boe,
        scrape_rba,
        scrape_boc,
        scrape_rbnz,
        scrape_sarb,
    ]
    
    new_forecasts = []
    for scraper in scrapers:
        try:
            result = scraper()
            if result and result.get("projections"):
                print(f"  ✅ {result['bank']}: {len(result['projections'])} projections found")
                for p in result["projections"]:
                    print(f"      {p['year']}: {p['value']}%")
                new_forecasts.append(result)
            else:
                print(f"  ⚠️  {scraper.__name__}: No projections extracted")
        except Exception as e:
            print(f"  ❌ {scraper.__name__}: Error - {e}")
    
    if not new_forecasts:
        print("\n❌ No forecasts extracted. Check scraper patterns.")
        return
    
    # Load current forecasts and compare
    current = load_current_forecasts()
    changes = compare_forecasts(current, new_forecasts)
    
    # Create draft JSON
    draft = {
        "_metadata": {
            "generated": datetime.now().isoformat(),
            "status": "DRAFT - REVIEW REQUIRED",
            "note": "Auto-extracted values may be incorrect. Verify against source URLs."
        },
        "forecasts": new_forecasts
    }
    
    os.makedirs("docs/data", exist_ok=True)
    
    with open("docs/data/cb_forecasts_draft.json", 'w') as f:
        json.dump(draft, f, indent=2)
    print(f"\n📄 Draft saved to docs/data/cb_forecasts_draft.json")
    
    # Create changes markdown for PR
    md = f"# Central Bank Forecast Changes\n\n"
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    md += "## ⚠️ Review Required\n\n"
    md += "The following values were auto-extracted and may need verification:\n\n"
    
    for forecast in new_forecasts:
        md += f"### {forecast['bank']} ({forecast['country']})\n"
        md += f"- **Source:** [{forecast['source']}]({forecast.get('source_url', '#')})\n"
        md += f"- **Metric:** {forecast['metric']}\n"
        md += "- **Projections:**\n"
        for p in forecast["projections"]:
            md += f"  - {p['year']}: **{p['value']}%**\n"
        md += "\n"
    
    if changes:
        md += "## Changes Detected\n\n"
        for change in changes:
            if change["old"] is None:
                md += f"- **{change['bank']}**: New bank added\n"
            else:
                md += f"- **{change['bank']}** {change['year']}: {change['old']}% → {change['new']}%\n"
    else:
        md += "## No Changes Detected\n\n"
        md += "Extracted values match current data.\n"
    
    with open("docs/data/cb_forecasts_changes.md", 'w') as f:
        f.write(md)
    print(f"📄 Changes summary saved to docs/data/cb_forecasts_changes.md")
    
    print("\n✅ Done! Review the draft and changes before merging.")


if __name__ == "__main__":
    main()
