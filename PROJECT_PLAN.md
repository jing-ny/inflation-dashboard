# Inflation Dashboard - Project Plan

**Last Updated:** 2026-01-26

This document tracks the architecture, priorities, and status of the Inflation Dashboard project.

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA FLOW (Target State)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Python Scripts                JSON Files              HTML/JS  │
│   ─────────────────────────────────────────────────────────────  │
│                                                                  │
│   fetch_historical_cpi.py  ──►  historical_cpi.json  ──►  All   │
│                                                           Pages  │
│   fetch_cb_forecasts.py    ──►  cb_forecasts.json    ──►        │
│                                                                  │
│   auto_scrape_cb_forecasts.py ──► (updates cb_forecasts.json)   │
│                                                                  │
│   fetch_imf_forecasts.py   ──►  imf_forecasts.json   ──►        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

GitHub Actions (automated):
  - update-data.yml: Weekly CPI + forecast data fetch (Mon 9am UTC)
  - auto-scrape-forecasts.yml: CB forecast scraping (Mon/Thu 10am UTC)
  - weekly-alert.yml: Status check (Mon 1pm UTC)
```

---

## File Structure

```
inflation-dashboard/
├── README.md                    # Project overview
├── LICENSE                      # MIT License
├── PROJECT_PLAN.md              # This file
├── METHODOLOGY.md               # Technical documentation
│
├── scripts/
│   ├── fetch_historical_cpi.py      # ✅ Fetches CPI from FRED/BLS/etc
│   ├── fetch_cb_forecasts.py        # ✅ Manual + API CB forecasts
│   ├── auto_scrape_cb_forecasts.py  # ✅ NEW: Auto-scrape CB publications
│   └── fetch_imf_forecasts.py       # ✅ Fetches IMF WEO projections
│
├── data/                        # Raw data (not in docs/)
│   ├── historical_cpi.json
│   ├── cb_forecasts.json
│   ├── imf_forecasts.json
│   └── scraper_state.json       # NEW: Tracks scraped publications
│
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview (loads from JSON dynamically)
│   ├── styles.css               # Shared styles
│   ├── country.js               # Shared country page logic
│   ├── us.html, uk.html, ...    # Country detail pages
│   └── data/
│       ├── historical_cpi.json  # Copied from data/
│       ├── cb_forecasts.json    # Copied from data/
│       └── imf_forecasts.json   # Copied from data/
│
└── .github/
    └── workflows/
        ├── update-data.yml          # Weekly data fetch (Mon 9am UTC)
        ├── auto-scrape-forecasts.yml # NEW: CB scraping (Mon/Thu 10am UTC)
        └── weekly-alert.yml         # Weekly status check (Mon 1pm UTC)
```

---

## Priority Status

### ✅ P0 — Critical (Data Accuracy & Consistency) - COMPLETE

| Task | Description | Status |
|------|-------------|--------|
| Fix data inconsistency | All pages read from same JSON sources | ✅ Done |
| Update CB forecasts | Match country.js to index.html (2025 data) | ✅ Done |
| Create cb_forecasts.json | Single source for CB forecast data | ✅ Done |
| Update README.md | Document current architecture | ✅ Done |
| Add LICENSE | MIT License file | ✅ Done |

### ✅ P1 — Important (Automation) - COMPLETE

| Task | Description | Status |
|------|-------------|--------|
| Build fetch_cb_forecasts.py | Script to update CB forecasts | ✅ Done |
| Fix GitHub Actions | Weekly alert was failing | ✅ Fixed |
| Update workflow | Run all fetch scripts weekly | ✅ Done |
| index.html dynamic loading | Load forecast table from JSON | ✅ Done |
| country.js dynamic loading | Load forecasts from cb_forecasts.json | ✅ Done |

### ✅ P2 — Auto-Scrape CB Forecasts - NEW (COMPLETE)

| Task | Description | Status |
|------|-------------|--------|
| Build auto_scrape_cb_forecasts.py | Web scraper for CB publications | ✅ Done |
| Publication detection | Detect new CB publications | ✅ Done |
| Forecast extraction | Parse forecasts from HTML pages | ✅ Done |
| GitHub Actions workflow | Auto-scrape Mon/Thu | ✅ Done |
| Manual fallback | Use manual data if scraping fails | ✅ Done |

### 🔲 P3 — Future Enhancements

| Task | Description | Status |
|------|-------------|--------|
| Add more countries | Japan, Singapore, India, etc. | 🔲 Not started |
| Email subscription | Alerts for material changes | 🔲 Not started |
| Supabase backend | Store forecast history | 🔲 Not started |
| Mobile optimization | Improve responsive design | 🔲 Not started |

---

## Auto-Scrape System Details

### Supported Central Banks

| Country | Central Bank | Publication | Frequency | Scraper Status |
|---------|--------------|-------------|-----------|----------------|
| 🇦🇺 AU | RBA | Statement on Monetary Policy | Quarterly (Feb, May, Aug, Nov) | ✅ Implemented |
| 🇪🇺 EA | ECB | Staff Macroeconomic Projections | Quarterly (Mar, Jun, Sep, Dec) | ✅ Implemented |
| 🇬🇧 UK | BoE | Monetary Policy Report | Quarterly (Feb, May, Aug, Nov) | ✅ Implemented |
| 🇨🇦 CA | BoC | Monetary Policy Report | Quarterly (Jan, Apr, Jul, Oct) | ✅ Implemented |
| 🇳🇿 NZ | RBNZ | Monetary Policy Statement | Quarterly (Feb, May, Aug, Nov) | ✅ Implemented |
| 🇿🇦 ZA | SARB | Monetary Policy Statement | Bi-monthly | ✅ Implemented |
| 🇺🇸 US | Fed | FOMC SEP | Quarterly | Manual only (API) |
| 🇨🇳 CN | - | IMF WEO | Semi-annual | Manual only (IMF) |

### How Auto-Scraping Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTO-SCRAPE WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PUBLICATION DETECTION                                        │
│     ├─ Fetch central bank index page                            │
│     ├─ Hash content to detect changes                           │
│     └─ Match publication pattern (regex)                        │
│                                                                  │
│  2. FORECAST EXTRACTION                                          │
│     ├─ Fetch publication/outlook page                           │
│     ├─ Parse HTML with BeautifulSoup                            │
│     ├─ Extract year/value pairs from tables or prose            │
│     └─ Validate and deduplicate                                 │
│                                                                  │
│  3. UPDATE & COMMIT                                              │
│     ├─ Update cb_forecasts.json                                 │
│     ├─ Update scraper_state.json                                │
│     └─ Git commit and push                                      │
│                                                                  │
│  4. FALLBACK                                                     │
│     └─ If scraping fails, use manual MANUAL_FORECASTS dict      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Running the Auto-Scraper Locally

```bash
# Check all sources
python scripts/auto_scrape_cb_forecasts.py

# Dry run (check only, don't update files)
python scripts/auto_scrape_cb_forecasts.py --dry-run

# Check specific country
python scripts/auto_scrape_cb_forecasts.py --country AU

# Force update (ignore publication cache)
python scripts/auto_scrape_cb_forecasts.py --force

# List all configured sources
python scripts/auto_scrape_cb_forecasts.py --list-sources
```

### Updating Manual Forecasts

If scraping fails or for countries without web scraping (US, CN), update the `MANUAL_FORECASTS` dict in `auto_scrape_cb_forecasts.py`:

```python
MANUAL_FORECASTS = {
    "US": {
        "source": "FOMC Summary of Economic Projections",
        "source_url": "https://www.federalreserve.gov/...",
        "last_updated": "December 2025",
        "measure": "PCE inflation (median projection)",
        "forecasts": [
            {"year": 2025, "value": 2.8},
            {"year": 2026, "value": 2.4},
            {"year": 2027, "value": 2.1},
        ]
    },
    # ... other countries
}
```

---

## GitHub Actions Workflows

### update-data.yml (Weekly Data Fetch)

- **Schedule:** Every Monday at 9:00 UTC
- **Runs:**
  1. `fetch_historical_cpi.py` → `historical_cpi.json`
  2. `fetch_cb_forecasts.py` → `cb_forecasts.json`
  3. `fetch_imf_forecasts.py` → `imf_forecasts.json`
  4. Copies to `docs/data/`
  5. Commits if changed
- **Status:** ✅ Working

### auto-scrape-forecasts.yml (CB Forecast Scraping)

- **Schedule:** Every Monday and Thursday at 10:00 UTC
- **Runs:**
  1. `auto_scrape_cb_forecasts.py` → checks for new CB publications
  2. Extracts forecasts from new publications
  3. Updates `cb_forecasts.json`
  4. Commits if changed
- **Manual Trigger:** Supports `--force`, `--country`, `--dry-run` options
- **Status:** ✅ NEW

### weekly-alert.yml (Status Check)

- **Schedule:** Every Monday at 13:00 UTC
- **Runs:** Simple data validation check
- **Status:** ✅ Working

---

## Data Sources

### Historical CPI (fetch_historical_cpi.py)

| Country | Source | API | Status |
|---------|--------|-----|--------|
| 🇺🇸 US | Bureau of Labor Statistics | FRED | ✅ Working |
| 🇪🇺 EA | Eurostat | FRED | ✅ Working |
| 🇬🇧 UK | ONS | FRED | ✅ Working |
| 🇦🇺 AU | ABS | FRED | ✅ Working (quarterly) |
| 🇨🇦 CA | Statistics Canada | FRED | ✅ Working |
| 🇳🇿 NZ | Stats NZ | FRED | ✅ Working (quarterly) |
| 🇿🇦 ZA | Stats SA | FRED | ✅ Working |
| 🇨🇳 CN | NBS | FRED | ✅ Working |

### Central Bank Forecasts (auto_scrape_cb_forecasts.py)

| Country | Source | Method | Status |
|---------|--------|--------|--------|
| 🇺🇸 US | FOMC SEP | Manual | ✅ Dec 2025 |
| 🇪🇺 EA | ECB Staff Projections | Auto-scrape | ✅ Dec 2025 |
| 🇬🇧 UK | BoE MPR | Auto-scrape | ✅ Nov 2025 |
| 🇦🇺 AU | RBA SMP | Auto-scrape | ✅ Nov 2025 |
| 🇨🇦 CA | BoC MPR | Auto-scrape | ✅ Oct 2025 |
| 🇳🇿 NZ | RBNZ MPS | Auto-scrape | ✅ Nov 2025 |
| 🇿🇦 ZA | SARB MPC | Auto-scrape | ✅ Nov 2025 |
| 🇨🇳 CN | IMF WEO | Manual | ✅ Oct 2025 |

---

## Session Recovery Guide

If starting a new session, run these commands to understand current state:

```bash
cd ~/Projects/inflation-dashboard

# Check git status
git status
git log --oneline -5

# Check data files exist
ls -la docs/data/

# Verify JSON structure
head -50 docs/data/cb_forecasts.json

# Check workflow status
cat .github/workflows/update-data.yml
cat .github/workflows/auto-scrape-forecasts.yml

# Test scraper locally
python scripts/auto_scrape_cb_forecasts.py --dry-run

# Test fetch scripts
python scripts/fetch_historical_cpi.py
python scripts/fetch_cb_forecasts.py --no-api
```

---

## Key Commits

| Date | Commit | Description |
|------|--------|-------------|
| 2026-01-26 | (latest) | Add auto-scrape CB forecasts system |
| 2026-01-26 | - | Update workflow to fetch all data sources |
| 2026-01-26 | - | Add fetch_cb_forecasts.py |
| 2026-01-26 | - | Fix weekly alert workflow |
| 2026-01-26 | 7a93704 | Single source of truth for forecasts |
| 2026-01-26 | 00d7bfa | Working state after revert |

---

## Maintenance Workflow

### When a Central Bank Releases New Forecasts

**Automatic (if scraper works):**
1. GitHub Action detects new publication
2. Extracts forecasts automatically
3. Commits to repository
4. Dashboard updates

**Manual (if scraper fails or for US/CN):**
1. Check the central bank website for new publication
2. Update `MANUAL_FORECASTS` in `auto_scrape_cb_forecasts.py`
3. Run `python scripts/auto_scrape_cb_forecasts.py`
4. Copy output: `cp data/cb_forecasts.json docs/data/`
5. Commit and push

### Adding a New Country

1. Add config to `SOURCES` dict in `auto_scrape_cb_forecasts.py`
2. Implement extractor function (e.g., `extract_xyz_forecasts`)
3. Add fallback to `MANUAL_FORECASTS`
4. Add country config to `fetch_historical_cpi.py`
5. Create country page HTML
6. Add to `index.html` display order
7. Test locally, then commit

---

## License

MIT License — See repository for details.
