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

import argparse
import json
import re
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
import ssl

# Use default SSL verification (secure)
ssl_context = ssl.create_default_context()

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


def _ecb_cell_text(cell_html):
    """Strip tags + decode common entities + normalise whitespace in a table cell."""
    t = re.sub(r'<[^>]+>', '', cell_html)
    t = t.replace('&nbsp;', ' ').replace('\xa0', ' ').replace('&amp;', '&')
    return re.sub(r'\s+', ' ', t).strip()


def _ecb_row_cells(tr_html):
    """Extract plain-text cells from a single <tr>...</tr> chunk."""
    cells_raw = re.findall(r'<t[dh]\b[^>]*>(.*?)</t[dh]>', tr_html, re.DOTALL | re.IGNORECASE)
    return [_ecb_cell_text(c) for c in cells_raw]


def _ecb_parse_float(s):
    """Parse an inflation-rate-like float. Reject obvious year strings."""
    s = s.strip()
    if re.fullmatch(r'20\d{2}', s):  # year, not a value
        return None
    try:
        v = float(s)
    except (ValueError, TypeError):
        return None
    # Headline HICP rarely strays outside ±20pp. Anything wider is suspicious.
    return v if -20.0 <= v <= 20.0 else None


def scrape_ecb():
    """Scrape ECB Staff Projections — headline HICP, baseline scenario.

    Parses the canonical summary table at the bottom of the ECB Staff
    Macroeconomic Projections page. Strategy: walk every <tr>; find a
    year-header row (>=4 consecutive cells matching ``20\\d{2}``); look at
    the next few rows for one whose first cell text is exactly ``"HICP"``
    (not ``"HICP excluding..."``, ``"HICP energy"``, etc.); take the 4
    numeric cells after the label, pair them with the year-header cells.

    Two reasons for the structured approach (vs. the prior regex-over-HTML
    and prose-fallback paths):

    1. ECB pages have many narrative paragraphs that mention "inflation" in
       close proximity to "HICP". Regex over prose happily picked up GDP
       growth, oil prices, etc. and emitted them as HICP values — same
       failure mode scrape_boe documents.

    2. The page actually contains multiple "HICP" cells: the alternative-
       scenarios table at the top has a sparse year structure (one year per
       row), while the projections-summary table at the bottom has the
       full 4-year horizon in one row. Anchoring on "year-header above,
       HICP-row beneath" reliably selects the summary table.

    Publication date is parsed from the URL (``projectionsYYYYMM``) so it
    survives even when the page-prose date wording changes.
    """
    print("📊 Scraping ECB...")
    url = None
    pub_year = pub_month = None

    # Discover the latest projections page from the index
    index_url = "https://www.ecb.europa.eu/pub/projections/html/index.en.html"
    index_html = fetch_url(index_url)
    if index_html:
        links = re.findall(
            r'href="([^"]*projections(\d{4})(\d{2})[^"]*\.en\.html)"', index_html
        )
        if links:
            rel, pub_year_str, pub_month_str = links[0]
            if rel.startswith('http'):
                url = rel
            elif rel.startswith('/'):
                url = "https://www.ecb.europa.eu" + rel
            else:
                url = "https://www.ecb.europa.eu/" + rel
            pub_year = int(pub_year_str)
            pub_month = int(pub_month_str)

    if not url:
        print("  ⚠️  Could not find ECB projections URL from index page")
        return None

    html = fetch_url(url)
    if not html:
        return None

    # Walk every <tr>; cache cells.
    trs = re.findall(r'<tr\b[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    rows = [_ecb_row_cells(tr) for tr in trs]

    # Find (year-header, HICP-row) pairs. Prefer the first one we find;
    # the summary table sits near the bottom of the page and is the only
    # spot where 4 consecutive years immediately precede a standalone
    # "HICP" cell with >=4 numeric values trailing.
    is_year = lambda s: bool(re.fullmatch(r'20\d{2}', s))

    chosen = None
    for i, cells in enumerate(rows):
        # Look for >=4 consecutive year cells starting somewhere in this row
        for start in range(len(cells)):
            run = []
            for c in cells[start:]:
                if is_year(c):
                    run.append(c)
                else:
                    break
            if len(run) < 4:
                continue
            # Year header found. Search the next few rows for "HICP" exactly.
            for j in range(i + 1, min(i + 5, len(rows))):
                nxt = rows[j]
                if 'HICP' not in nxt:
                    continue
                idx = nxt.index('HICP')
                vals = []
                for c in nxt[idx + 1:]:
                    v = _ecb_parse_float(c)
                    if v is not None:
                        vals.append(v)
                    if len(vals) >= 4:
                        break
                if len(vals) >= 4:
                    chosen = {'years': run[:4], 'values': vals[:4]}
                    break
            if chosen:
                break
        if chosen:
            break

    if not chosen:
        print("  ⚠️  scrape_ecb: could not locate canonical HICP summary table "
              "(year-header row followed by 'HICP' row with >=4 numeric cells)")
        return None

    projections = [
        {"year": y, "value": v} for y, v in zip(chosen['years'], chosen['values'])
    ]

    result = {
        "bank": "European Central Bank",
        "country": "EA",
        "metric": "HICP Inflation (Baseline)",
        "source": "ECB Staff Projections",
        "source_url": url,
        "projections": projections,
    }
    if pub_year and pub_month:
        result["source_date"] = f"{pub_year}-{pub_month:02d}-01"
    return result


def scrape_boe():
    """Scrape Bank of England Monetary Policy Report.

    Note: HTML prose extraction is currently disabled. The MPR mentions
    headline CPI, services inflation, food price inflation, AWE wage
    growth, world GDP, etc. all in the same paragraph style — regex over
    prose cannot reliably distinguish them and was silently overwriting
    curated forecasts with values like "food price inflation 4.6% by
    September 2026" reinterpreted as headline CPI.

    The URL-discovery half still runs so that:
      - the workflow no longer fails on a 404 index page, and
      - we surface a clear log line pointing at the MPR for human review.

    Returning None keeps the existing curated UK entry intact.
    Proper structured-table extraction tracked in #10.
    """
    print("📊 Scraping BoE...")

    # The dedicated /monetary-policy-report index page was retired sometime
    # before 2026-04-30 (it now 404s). The /monetary-policy hub page links
    # to the latest MPR with the same /monetary-policy-report/YYYY/<month>
    # URL scheme, so we use it as the index instead.
    url = None
    index_url = "https://www.bankofengland.co.uk/monetary-policy"
    index_html = fetch_url(index_url)

    if index_html:
        links = re.findall(r'href="(/monetary-policy-report/\d{4}/[^"]+)"', index_html)
        if links:
            url = "https://www.bankofengland.co.uk" + links[0]

    if not url:
        print("  ⚠️  Could not find BoE MPR URL from index page")
        return None

    print(f"  ℹ️  Found latest MPR: {url}")
    print("  ⏸️  scrape_boe: extractor disabled until structured-table parsing lands; "
          "preserving curated UK forecast")
    return None


def scrape_rba():
    """Scrape RBA Statement on Monetary Policy.

    The RBA SMP folder layout is /publications/smp/YYYY/<month>/ containing
    overview.html, contents.html, and a PDF — there is no per-chapter
    economic-outlook.html in recent SMPs (the old URL we used 404s).

    overview.html contains a clean projection table with year-ended Dec/June
    columns. We parse the "Trimmed mean inflation" row (RBA's preferred
    underlying measure) and emit only the Dec columns as year-keyed values.
    """
    print("📊 Scraping RBA...")

    index_url = "https://www.rba.gov.au/publications/smp/"
    index_html = fetch_url(index_url)
    if not index_html:
        return None

    folder_links = re.findall(r'href="(/publications/smp/\d{4}/\w+/)"', index_html)
    if not folder_links:
        print("  ⚠️  Could not find RBA SMP folder from index page")
        return None

    folder = folder_links[0]
    url = "https://www.rba.gov.au" + folder + "overview.html"

    html = fetch_url(url)
    if not html:
        return None

    # Strip tags + normalise whitespace; the projection table is in plain
    # text once HTML is removed.
    clean = re.sub(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', ' ', html, flags=re.I)
    clean = re.sub(r'<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>', ' ', clean, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', clean)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    header_match = re.search(
        r'Year-?ended\s+'
        r'((?:(?:Dec|June|March|Sept(?:ember)?)\s+\d{4}\s*){4,8})',
        text)
    if not header_match:
        print("  ⚠️  Could not locate 'Year-ended' header in RBA overview")
        return None

    month_years = re.findall(r'(Dec|June|March|Sept(?:ember)?)\s+(\d{4})',
                             header_match.group(1))
    n = len(month_years)
    if n < 4:
        print(f"  ⚠️  RBA header had only {n} columns; expected ≥4")
        return None

    row_match = re.search(
        r'Trimmed mean inflation\s+' + r'(\d+\.\d+)\s+' * (n - 1) + r'(\d+\.\d+)',
        text)
    if not row_match:
        print("  ⚠️  Could not locate 'Trimmed mean inflation' row in RBA overview")
        return None

    values = [float(v) for v in row_match.groups()]

    projections = []
    seen_years = set()
    for (month, year), val in zip(month_years, values):
        if month != 'Dec':
            continue
        if not (0 < val < 15):
            continue
        if year in seen_years:
            continue
        projections.append({"year": year, "value": val})
        seen_years.add(year)

    if not projections:
        print("  ⚠️  RBA overview parsed but no usable Dec projections")
        return None

    # Source date as YYYY-MM-DD (day-1 anchor — RBA SMPs publish in the
    # first half of the named month; the merge layer converts to display
    # form for the UI).
    folder_match = re.search(r'/(\d{4})/(\w+)/$', folder)
    source_date = None
    if folder_match:
        from datetime import date as _date
        year_str, month_str = folder_match.groups()
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        try:
            month_num = months.index(month_str.lower()[:3]) + 1
            source_date = _date(int(year_str), month_num, 1).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            pass

    result = {
        "bank": "Reserve Bank of Australia",
        "country": "AU",
        "metric": "Trimmed mean inflation",
        "source": "Statement on Monetary Policy",
        "source_url": url,
        "projections": projections,
    }
    if source_date:
        result["source_date"] = source_date
    return result


def scrape_boc():
    """Scrape Bank of Canada Monetary Policy Report.

    BoC restructured its MPR URLs: old reports lived at
    /YYYY/MM/mpr-YYYY-MM-DD/ but current ones are at
    /publications/mpr/mpr-YYYY-MM-DD/. The MPR is split across chapter
    sub-pages; the projection tables live on the /projections/ sub-page.

    Table 2 (annual) is the cleanest source: header is plain "2025 2026
    2027 2028" and the row label is "CPI inflation". We strip the
    previous-report comparison values (in parens) and align values to
    years from the header.
    """
    print("📊 Scraping BoC...")

    index_url = "https://www.bankofcanada.ca/publications/mpr/"
    index_html = fetch_url(index_url)
    if not index_html:
        return None

    # New URL scheme. Pattern: /publications/mpr/mpr-YYYY-MM-DD/
    links = re.findall(
        r'href="(https://www\.bankofcanada\.ca/publications/mpr/mpr-\d{4}-\d{2}-\d{2}/)"',
        index_html,
    )
    if not links:
        print("  ⚠️  Could not find BoC MPR URL from index page")
        return None

    mpr_url = links[0]
    projections_url = mpr_url.rstrip("/") + "/projections/"

    html = fetch_url(projections_url)
    if not html:
        return None

    clean = re.sub(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', ' ', html, flags=re.I)
    clean = re.sub(r'<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>', ' ', clean, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', clean)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&ndash;|&minus;', '-', text)
    text = re.sub(r'\s+', ' ', text)

    # Capture the CPI inflation row of Table 2 (annual). It ends at the
    # next memo / footnote / source marker.
    row_match = re.search(
        r'CPI inflation\s+([\d\.\s\(\)\-]+?)(?=Core inflation|\* Numbers|Sources)',
        text,
    )
    if not row_match:
        print("  ⚠️  Could not locate 'CPI inflation' row in BoC projections page")
        return None

    # Strip paren content (previous-report comparison values).
    row_clean = re.sub(r'\([^)]*\)', ' ', row_match.group(1))
    raw_values = [float(v) for v in re.findall(r'\d+\.\d+', row_clean)]
    if not raw_values:
        print("  ⚠️  BoC CPI row matched but no numeric values parsed")
        return None

    # Find the year header that precedes the CPI row — pick the last
    # sequence of 4+ consecutive years (YYYY YYYY ...) before the match.
    header_iter = list(
        re.finditer(r'((?:20\d{2}\s+){3,7}20\d{2})', text, 0)
    )
    header_iter = [h for h in header_iter if h.end() <= row_match.start()]
    if not header_iter:
        print("  ⚠️  Could not locate year header before BoC CPI row")
        return None

    years = re.findall(r'20\d{2}', header_iter[-1].group(1))
    n = min(len(years), len(raw_values))
    projections = []
    seen_years = set()
    for year, val in zip(years[:n], raw_values[:n]):
        if not (0 < val < 15) or year in seen_years:
            continue
        projections.append({"year": year, "value": val})
        seen_years.add(year)

    if not projections:
        print("  ⚠️  BoC projection row parsed but no usable year/value pairs")
        return None

    # Source date as YYYY-MM-DD from the URL (e.g. /mpr-2026-04-29/ →
    # 2026-04-29). Merge layer converts to display form for the UI.
    date_match = re.search(r'/mpr-(\d{4})-(\d{2})-(\d{2})/', mpr_url)
    source_date = None
    if date_match:
        year_str, month_str, day_str = date_match.groups()
        source_date = f"{year_str}-{month_str}-{day_str}"

    result = {
        "bank": "Bank of Canada",
        "country": "CA",
        "metric": "CPI Inflation",
        "source": "Monetary Policy Report",
        "source_url": projections_url,
        "projections": projections,
    }
    if source_date:
        result["source_date"] = source_date
    return result


def scrape_rbnz():
    """Scrape RBNZ Monetary Policy Statement."""
    print("📊 Scraping RBNZ...")
    
    # Try to find latest MPS from index page
    url = None
    index_url = "https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement"
    index_html = fetch_url(index_url)

    if index_html:
        links = re.findall(r'href="(/monetary-policy/monetary-policy-statement/mps-[^"]+)"', index_html)
        if links:
            url = "https://www.rbnz.govt.nz" + links[0]

    if not url:
        print("  ⚠️  Could not find RBNZ MPS URL from index page")
        return None
    
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


def _discover_fed_sep_url():
    """Find the URL of the most recent Fed SEP from the FOMC calendar page.

    Returns (url, pub_date) or (None, None) if none found.
    """
    index_url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    html = fetch_url(index_url)
    if not html:
        return None, None

    # Pattern: href="/monetarypolicy/fomcprojtabl20260318.htm"
    links = re.findall(r'href="(/monetarypolicy/fomcprojtabl(\d{8})\.htm)"', html)
    if not links:
        return None, None

    links.sort(key=lambda x: x[1], reverse=True)
    rel, date_str = links[0]
    url = f"https://www.federalreserve.gov{rel}"
    pub_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return url, pub_date


def _normalize_year_label(label):
    """'2026' stays '2026'; 'Longer run' -> 'longer_run'."""
    label = label.strip()
    if re.match(r'^\d{4}$', label):
        return label
    if "longer" in label.lower():
        return "longer_run"
    return label


def scrape_fed():
    """Scrape the Fed SEP for median PCE inflation projections."""
    print("📊 Scraping Fed SEP...")

    url, pub_date = _discover_fed_sep_url()
    if not url:
        print("  ⚠️  Could not discover Fed SEP URL from FOMC calendar")
        return None

    html = fetch_url(url)
    if not html:
        return None

    # Column year labels live in the header row as <th ... id="xt1bN">YEAR</th>
    # IDs b1..b4 are the Median block; b5..b8 Central Tendency; b9..b12 Range.
    header_matches = re.findall(r'<th[^>]*id="xt1b(\d+)"[^>]*>\s*([^<]+?)\s*</th>', html)
    header_map = {int(n): label for n, label in header_matches}
    median_years = [header_map.get(i) for i in (1, 2, 3, 4)]
    if not all(median_years):
        print(f"  ⚠️  Could not extract year header (got {median_years})")
        return None

    # PCE inflation row — top-level, class is exactly "stub" (not "stub in1").
    # The row contains 12 <td class="data"> cells; first 4 are the Medians.
    row = re.search(
        r'<th class="stub"[^>]*>\s*PCE inflation\s*</th>(.*?)</tr>',
        html, re.DOTALL
    )
    if not row:
        print("  ⚠️  PCE inflation row not found")
        return None

    value_matches = re.findall(r'<td class="data"[^>]*>\s*([\d.]+)\s*</td>', row.group(1))
    values = [float(v) for v in value_matches[:4]]
    if len(values) < 4:
        print(f"  ⚠️  Incomplete Median values (got {values})")
        return None

    projections = [
        {"year": _normalize_year_label(y), "value": v}
        for y, v in zip(median_years, values)
    ]

    return {
        "bank": "Federal Reserve",
        "country": "US",
        "metric": "PCE Inflation (Median FOMC projection)",
        "source": "Fed Summary of Economic Projections",
        "source_url": url,
        "source_date": pub_date,
        "projections": projections,
    }


def _discover_boj_outlook_pdf():
    """Find the URL of the most recent BoJ Outlook full-text PDF.

    Returns (url, pub_date) or (None, None).
    """
    index_url = "https://www.boj.or.jp/en/mopo/outlook/index.htm"
    html = fetch_url(index_url)
    if not html:
        return None, None

    # Full-text PDFs end in 'b.pdf'; summaries in 'a.pdf'. Pattern: gor<YY><MM>b.pdf
    links = re.findall(r'href="([^"]*?/gor(\d{2})(\d{2})b\.pdf)"', html)
    if not links:
        return None, None

    # Convert 2-digit year to 4-digit; sort descending by YYYYMM
    def sort_key(item):
        yy, mm = int(item[1]), int(item[2])
        year = 2000 + yy if yy < 90 else 1900 + yy
        return year * 100 + mm

    links.sort(key=sort_key, reverse=True)
    rel, yy, mm = links[0]
    if rel.startswith("http"):
        url = rel
    elif rel.startswith("/"):
        url = "https://www.boj.or.jp" + rel
    else:
        url = "https://www.boj.or.jp/en/mopo/outlook/" + rel

    pub_date = f"20{yy}-{mm}-01"
    return url, pub_date


def _fetch_pdf_text(url):
    """Download a PDF and return concatenated text of all pages."""
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=60, context=ssl_context) as response:
            pdf_bytes = response.read()
    except URLError as e:
        print(f"  ❌ Failed to fetch PDF {url}: {e}")
        return None

    try:
        from pypdf import PdfReader
    except ImportError:
        print("  ❌ pypdf not installed — add it to workflow requirements")
        return None

    import io
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def scrape_boj():
    """Scrape BoJ Outlook for the Majority of the Policy Board Members' median
    CPI (all items less fresh food) forecasts. Fiscal-year basis."""
    print("📊 Scraping BoJ Outlook...")

    url, pub_date = _discover_boj_outlook_pdf()
    if not url:
        print("  ⚠️  Could not discover BoJ Outlook PDF from index")
        return None

    text = _fetch_pdf_text(url)
    if not text:
        return None

    # Confirm we're on the right table
    if "CPI (all items less fresh food)" not in text:
        print("  ⚠️  Forecast table (CPI less fresh food) not found in PDF")
        return None

    # Per fiscal year, a *forecast* row has three [median] brackets in order:
    # 1) Real GDP, 2) CPI (all items less fresh food), 3) CPI less fresh food & energy.
    # We want #2.
    #
    # Once a fiscal year's CPI is realised, the BoJ table promotes it to actual
    # data and the row shape becomes "+X.X to +X.X [+X.X] +Y.Y +Z.Z" — i.e. only
    # the GDP figure stays bracketed (because real GDP for that FY is still a
    # provisional median), while CPI and core-core appear as bare numbers. The
    # April 2026 Outlook is the first publication where FY2025 sits in this
    # promoted state (note 4: "The CPI figures for fiscal 2025 are actual
    # values.").
    #
    # The original regex required three brackets per row and didn't anchor on
    # row boundaries, so on the promoted FY it slid into the "Forecasts made
    # in <month> <year>" comparison row underneath and grabbed that row's GDP
    # median as if it were the current FY's CPI (e.g. emitted 2025: 0.9% when
    # the actual figure is 2.7%).
    #
    # Fix: forbid the regex from spanning into either the next "Fiscal YYYY"
    # row or a "Forecasts made in" comparison block. Rows where the CPI cell
    # has been promoted to actual data won't match (only one bracket inside
    # the row segment), so we silently skip them — actual CPI is sourced from
    # historical_cpi.json, not from the forecast appendix.
    boundary = r'(?:(?!Fiscal\s+\d{4}|Forecasts\s+made\s+in)[\s\S])*?'
    row_pattern = re.compile(
        r'Fiscal\s+(\d{4})\b'
        + boundary + r'\[\s*([+-]?\d+\.\d+)\s*\]'   # GDP median
        + boundary + r'\[\s*([+-]?\d+\.\d+)\s*\]'   # CPI (less fresh food) median
        + boundary + r'\[\s*([+-]?\d+\.\d+)\s*\]'   # core-core median
    )

    projections = []
    seen_years = set()
    for year, _gdp, cpi, _cc in row_pattern.findall(text):
        if year in seen_years:
            continue
        seen_years.add(year)
        # Strip leading '+' but preserve negative sign
        value = float(cpi)
        projections.append({"year": year, "value": round(value, 2)})

    if not projections:
        print("  ⚠️  Could not parse forecast rows")
        return None

    return {
        "bank": "Bank of Japan",
        "country": "JP",
        "metric": "CPI excluding fresh food (Median Policy Board projection, fiscal year)",
        "source": "BoJ Outlook for Economic Activity and Prices",
        "source_url": url,
        "source_date": pub_date,
        "projections": projections,
    }


def scrape_bcb():
    """Fetch the latest Focus survey median IPCA forecasts via BCB Olinda API.

    Focus is published every Monday and tracks market-consensus expectations.
    We pull the most recent business day's medians for 2026..2028.
    """
    print("📊 Scraping BCB Focus survey...")

    # Olinda OData endpoint for annual market expectations.
    # baseCalculo=0 = full sample; we want the most recent observation per year.
    base = ("https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
            "ExpectativasMercadoAnuais")
    # Pre-encoded filter to avoid quote escaping pitfalls in urlencode.
    today_year = datetime.now().year
    query = (
        f"?$top=200"
        f"&$filter=Indicador%20eq%20'IPCA'"
        f"%20and%20baseCalculo%20eq%200"
        f"%20and%20DataReferencia%20ge%20'{today_year}'"
        f"%20and%20DataReferencia%20le%20'{today_year + 4}'"
        f"&$orderby=Data%20desc"
        f"&$format=application/json"
    )
    url = base + query

    raw = fetch_url(url)
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  Could not decode Focus JSON: {e}")
        return None

    rows = data.get("value", [])
    if not rows:
        print("  ⚠️  Focus API returned no records")
        return None

    # Keep only the most recent median per reference year.
    latest_by_year = {}
    latest_obs_date = None
    for row in rows:
        year = row.get("DataReferencia")
        if year not in latest_by_year and row.get("Mediana") is not None:
            latest_by_year[year] = row
            if latest_obs_date is None:
                latest_obs_date = row.get("Data")

    if not latest_by_year:
        return None

    projections = []
    for year in sorted(latest_by_year):
        v = latest_by_year[year]
        projections.append({"year": year, "value": round(float(v["Mediana"]), 2)})

    return {
        "bank": "Banco Central do Brasil",
        "country": "BR",
        "metric": "IPCA — Focus survey median",
        "source": "BCB Focus Market Readout (Olinda API)",
        "source_url": "https://www.bcb.gov.br/en/publications/focusmarketreadout",
        "source_date": latest_obs_date,
        "projections": projections,
    }


def scrape_sarb():
    """Scrape SARB MPC Statement.

    Note: extraction is currently disabled. Two compounding issues:
      1. The previous URL (.../monetary-policy-statements/{YEAR}) 404s — that
         path scheme was retired. The replacement landing page
         /en/home/publications/statements/mpc-statements returns HTTP 200 but
         is JS/AEM-rendered: at time of writing it even shows "We are
         currently experiencing technical difficulties" on its own listing
         widget and exposes no individual statement links in static HTML.
      2. The original prose regex was a generic "decimal-near-year" match,
         which on a real MPC statement also catches policy-rate references,
         GDP growth, and core/food/services inflation — silently overwriting
         curated forecasts.

    We hit the new landing page so the workflow no longer 404s, then return
    None to preserve the curated ZA entry. Proper extraction (PDF parsing
    once individual statement links are reachable) tracked in #12.
    """
    print("📊 Scraping SARB...")

    index_url = "https://www.resbank.co.za/en/home/publications/statements/mpc-statements"
    html = fetch_url(index_url)
    if not html:
        return None

    print(f"  ℹ️  SARB MPC statements landing page reachable: {index_url}")
    print("  ⏸️  scrape_sarb: extractor disabled — listing page is JS-rendered "
          "and lacks static statement links; preserving curated ZA forecast")
    return None


def load_current_forecasts():
    """Load current cb_forecasts.json for comparison."""
    path = "docs/data/cb_forecasts.json"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"forecasts": []}


def compare_forecasts(current, new):
    """Compare current and new forecasts, return changes.

    `current` is the committed cb_forecasts.json with shape
        {"forecasts": {"US": {"projections": {"2026": 2.7, ...}, ...}, ...}}
    `new` is a list of scraper results with shape
        [{"country": "US", "bank": "Federal Reserve",
          "projections": [{"year": "2026", "value": 2.7}, ...]}, ...]
    """
    changes = []
    current_by_country = current.get("forecasts", {}) or {}

    for new_forecast in new:
        country = new_forecast.get("country")
        bank = new_forecast.get("bank", country)
        current_entry = current_by_country.get(country, {}) if isinstance(current_by_country, dict) else {}
        old_proj = current_entry.get("projections", {}) if isinstance(current_entry, dict) else {}
        new_proj = {p["year"]: p["value"] for p in new_forecast.get("projections", [])}

        if not old_proj:
            changes.append({"bank": bank, "country": country, "year": "all",
                            "old": None, "new": new_proj})
            continue

        for year, value in new_proj.items():
            old_value = old_proj.get(year)
            if old_value is None:
                changes.append({"bank": bank, "country": country, "year": year,
                                "old": None, "new": value})
            elif abs(float(old_value) - float(value)) > 0.01:
                changes.append({"bank": bank, "country": country, "year": year,
                                "old": old_value, "new": value})

    return changes


COUNTRY_SCRAPERS = {
    "US": scrape_fed,
    "JP": scrape_boj,
    "BR": scrape_bcb,
    "EA": scrape_ecb,
    "UK": scrape_boe,
    "AU": scrape_rba,
    "CA": scrape_boc,
    "NZ": scrape_rbnz,
    "ZA": scrape_sarb,
}

MERGE_THRESHOLD_PP = 1.0  # any year-over-year change larger than this blocks auto-merge


def _normalise_publication_date(source_date: str) -> str:
    """Render a scraper-provided source_date (YYYY-MM-DD) as 'Month YYYY' for the UI.

    All scrapers now emit `source_date` in canonical YYYY-MM-DD form (see #25).
    The dashboard renders this string verbatim ([docs/index.html:347](docs/index.html)),
    so we normalise here to the long-form 'Month YYYY' style used by the
    curated entries.

    Falls back to the raw string for safety — e.g. if a future scraper emits
    a different shape, the workflow still completes and the resulting value
    surfaces in the next email + git diff for human review (CLAUDE.md #5:
    don't silence the alarm).
    """
    s = (source_date or "").strip()
    if not s:
        return s
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%B %Y")
    except ValueError:
        return s


def merge_into_main(new_forecasts, dry_run=False):
    """Merge scraped forecasts directly into cb_forecasts.json.

    Preserves all curated fields (flag, note, key_quote, policy_rate, etc.);
    only rewrites projections, source_url, and publication_date.

    Anomaly gate: if any year's delta exceeds MERGE_THRESHOLD_PP, that country
    is SKIPPED (not merged) and reported so a human can verify.

    Returns (merged_countries: list, blocked: list[{country, reason, ...}]).
    """
    path = "docs/data/cb_forecasts.json"
    if not os.path.exists(path):
        return [], [{"reason": "cb_forecasts.json missing"}]

    with open(path, 'r') as f:
        data = json.load(f)

    country_data = data.get("forecasts", {})
    merged = []
    blocked = []

    for fc in new_forecasts:
        country = fc.get("country")
        if not country or country not in country_data:
            blocked.append({"country": country, "reason": "country_not_in_forecasts"})
            continue

        entry = country_data[country]
        old_proj = entry.get("projections", {}) or {}
        new_proj = {p["year"]: p["value"] for p in fc.get("projections", [])}

        # Anomaly gate: largest absolute delta on any matching year
        max_delta = 0.0
        for year, value in new_proj.items():
            old_value = old_proj.get(year)
            if old_value is not None:
                max_delta = max(max_delta, abs(float(old_value) - float(value)))

        if max_delta > MERGE_THRESHOLD_PP:
            blocked.append({
                "country": country,
                "reason": f"step {max_delta:.2f}pp exceeds {MERGE_THRESHOLD_PP}pp",
                "old": old_proj,
                "new": new_proj,
            })
            continue

        # Apply merge — rewrite projections and source metadata only
        entry["projections"] = new_proj
        if fc.get("source_url"):
            entry["source_url"] = fc["source_url"]
        if fc.get("source_date"):
            entry["publication_date"] = _normalise_publication_date(fc["source_date"])
        merged.append({
            "country": country,
            "bank": fc.get("bank"),
            "projections": new_proj,
            "source_url": fc.get("source_url"),
        })

    if merged:
        data.setdefault("metadata", {})["last_updated"] = datetime.now().strftime("%B %Y")
        if not dry_run:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write('\n')

    return merged, blocked


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Auto-scrape central bank inflation forecasts."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force scrape even if a recent draft already exists",
    )
    parser.add_argument(
        "--country",
        type=str,
        default=None,
        help="Scrape only the specified country code (e.g. UK, EA, AU)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Run scrapers but do not write output files",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help=("Auto-merge scraped projections directly into cb_forecasts.json. "
              "Changes larger than %.1fpp/year are blocked and written to the "
              "draft review path instead." % MERGE_THRESHOLD_PP),
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("🔄 Auto-scraping Central Bank Forecasts...")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if args.dry_run:
        print("   Mode: DRY RUN (no files will be written)")
    if args.country:
        print(f"   Country filter: {args.country}")
    if args.force:
        print("   Force: enabled")
    print()

    # Check for existing draft unless --force
    draft_path = "docs/data/cb_forecasts_draft.json"
    if not args.force and os.path.exists(draft_path):
        mod_time = datetime.fromtimestamp(os.path.getmtime(draft_path))
        age_hours = (datetime.now() - mod_time).total_seconds() / 3600
        if age_hours < 12:
            print(f"⚠️  Recent draft exists ({age_hours:.1f}h old). Use --force to re-scrape.")
            return

    # Select scrapers
    if args.country:
        code = args.country.upper()
        if code not in COUNTRY_SCRAPERS:
            print(f"❌ Unknown country code: {code}")
            print(f"   Available: {', '.join(COUNTRY_SCRAPERS.keys())}")
            return
        scrapers = [COUNTRY_SCRAPERS[code]]
    else:
        scrapers = list(COUNTRY_SCRAPERS.values())

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
    
    # Auto-merge path — rewrites cb_forecasts.json directly with anomaly gate
    merged = []
    blocked = []
    if args.merge:
        merged, blocked = merge_into_main(new_forecasts, dry_run=args.dry_run)
        if merged:
            print(f"\n✅ Auto-merged {len(merged)} countr{'y' if len(merged)==1 else 'ies'} into cb_forecasts.json:")
            for m in merged:
                print(f"   - {m['country']} ({m['bank']}): {m['projections']}")
        if blocked:
            print(f"\n⚠️  {len(blocked)} block(s) written to draft for review:")
            for b in blocked:
                print(f"   - {b.get('country','?')}: {b.get('reason')}")

    if args.dry_run:
        if args.merge:
            print("\n🏁 Dry run — no writes.")
        else:
            print("\n🏁 Dry run complete. No files written.")
            print(f"   Forecasts extracted: {len(new_forecasts)}")
            print(f"   Changes detected: {len(changes)}")
        return

    os.makedirs("docs/data", exist_ok=True)

    # Always write the changes-summary markdown after a non-dry run. The
    # downstream email-notification step in .github/workflows/auto-scrape-cb-
    # forecasts.yml reads this file to populate the email subject (country
    # codes) and body (per-country diffs). When --merge succeeded with zero
    # blocks (the common happy path), skipping this write left the email
    # showing the "(no cb_forecasts_changes.md on disk)" footer with no
    # detail at all — observed live in the 2026-05-12 run.
    blocked_countries = {b.get("country") for b in blocked}
    changed_countries = {c["country"] for c in changes} | blocked_countries

    md = "# Central Bank Forecast Changes\n\n"
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    if args.merge:
        if merged:
            non_block_merged = [m for m in merged if m["country"] not in blocked_countries]
            md += f"**Auto-merged ({len(non_block_merged)}):** "
            md += ", ".join(f"{m['country']}" for m in non_block_merged) + "\n\n"
        if blocked:
            md += f"**Blocked, written to draft ({len(blocked)}):** "
            md += ", ".join(f"{b.get('country','?')} ({b.get('reason','')})" for b in blocked) + "\n\n"
        if not changed_countries:
            md += "_All scraped values match the curated forecasts — nothing to review._\n\n"
    else:
        md += "## ⚠️ Review Required\n\n"
        md += "The following values were auto-extracted and may need verification:\n\n"

    # Emit `### Bank (CC)` headers only for banks that actually changed.
    # The email step parses these to build the subject country list, so
    # listing every scraped bank would produce noisy "updated — US, JP,
    # BR, EA, AU, CA" subjects every run.
    for forecast in new_forecasts:
        country = forecast["country"]
        if args.merge and country not in changed_countries:
            continue
        md += f"### {forecast['bank']} ({country})\n"
        md += f"- **Source:** [{forecast['source']}]({forecast.get('source_url', '#')})\n"
        md += f"- **Metric:** {forecast['metric']}\n"
        if forecast.get('source_date'):
            md += f"- **Publication:** {forecast['source_date']}\n"
        md += "- **Projections:**\n"
        for p in forecast["projections"]:
            md += f"  - {p['year']}: **{p['value']}%**\n"
        md += "\n"

    # "Changes Detected" section: only value-changes between old and new.
    # Brand-new years/banks are already itemised under each bank's
    # projections list above, so duplicating them here as "New bank added"
    # is noisy and misleading (compare_forecasts emits old=None for both
    # "country never seen before" and "year never seen before").
    value_changes = [c for c in changes if c["old"] is not None]
    new_banks = [c for c in changes if c["old"] is None and c["year"] == "all"]
    if value_changes or new_banks:
        md += "## Changes Detected\n\n"
        for change in new_banks:
            md += f"- **{change['bank']}**: new bank added to dataset\n"
        for change in value_changes:
            md += f"- **{change['bank']}** {change['year']}: {change['old']}% → {change['new']}%\n"
    elif args.merge and not blocked:
        md += "## No Changes Detected\n\n"
        md += "Extracted values match the curated forecasts.\n"

    with open("docs/data/cb_forecasts_changes.md", 'w') as f:
        f.write(md)
    print("\n📄 Changes summary saved to docs/data/cb_forecasts_changes.md")

    # Draft JSON: emit when running without --merge (full draft is the
    # whole point of that mode) or when --merge produced blocks for review.
    if (not args.merge) or blocked:
        with open("docs/data/cb_forecasts_draft.json", 'w') as f:
            json.dump(draft, f, indent=2)
        print("📄 Draft saved to docs/data/cb_forecasts_draft.json")

    print("\n✅ Done! Review the draft and changes before merging.")


if __name__ == "__main__":
    main()
