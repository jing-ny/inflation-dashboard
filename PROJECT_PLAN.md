# Inflation Dashboard - Project Plan & Architecture

**Last Updated:** January 26, 2026  
**Purpose:** Reference document to maintain consistency across sessions and recover from any disruptions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [Target Architecture](#target-architecture)
4. [Data Flow](#data-flow)
5. [File Structure](#file-structure)
6. [Scripts & Automation](#scripts--automation)
7. [Known Issues & Fixes Needed](#known-issues--fixes-needed)
8. [Priority List](#priority-list)
9. [Session Recovery Guide](#session-recovery-guide)
10. [README Template](#readme-template)

---

## Project Overview

**Name:** Inflation, Officially  
**URL:** https://jing-ny.github.io/inflation-dashboard/  
**Repo:** https://github.com/jing-ny/inflation-dashboard  

**Purpose:** A source-first dashboard tracking official CPI inflation data and central bank forecasts across 8 major economies.

**Countries Covered:**
| Code | Country | CPI Source | Central Bank | Frequency |
|------|---------|------------|--------------|-----------|
| US | United States | BLS | Federal Reserve | Monthly |
| EA | Euro Area | Eurostat | ECB | Monthly |
| UK | United Kingdom | ONS | Bank of England | Monthly |
| AU | Australia | ABS | RBA | Quarterly |
| CA | Canada | Statistics Canada | Bank of Canada | Monthly |
| NZ | New Zealand | Stats NZ | RBNZ | Quarterly |
| ZA | South Africa | Stats SA | SARB | Monthly |
| CN | China | NBS | PBOC | Monthly |

---

## Current State (as of Jan 26, 2026)

### What Works
- ✅ Overview page (`index.html`) displays summary table
- ✅ Overview page has Central Bank Outlook forecast table
- ✅ Individual country pages (`us.html`, `uk.html`, etc.) load and display
- ✅ Country pages load CPI data from `data/historical_cpi.json`
- ✅ Country pages show forecast comparison (Central Bank vs IMF)
- ✅ `fetch_historical_cpi.py` fetches CPI data from FRED API
- ✅ `fetch_imf_forecasts.py` fetches IMF WEO forecasts

### What's Broken
- ❌ **Data inconsistency:** `index.html` has hardcoded forecasts in HTML that differ from `country.js`
- ❌ **README.md** is outdated (doesn't reflect current architecture)
- ❌ **Central bank forecasts** in `country.js` are from 2024, not 2025
- ❌ **No single source of truth** for forecast data

---

## Target Architecture

### Core Principle: No Hardcoded Data in HTML/JS

All data should flow from JSON files that are updated by Python scripts:

```
Python Scripts (fetch data)
        ↓
    JSON Files (single source of truth)
        ↓
    HTML/JS Pages (read and display)
```

### Data Files (in `docs/data/`)

| File | Contents | Updated By |
|------|----------|------------|
| `historical_cpi.json` | 10-year CPI history + latest/previous readings | `fetch_historical_cpi.py` |
| `imf_forecasts.json` | IMF WEO inflation projections | `fetch_imf_forecasts.py` |
| `cb_forecasts.json` | Central bank forecasts (Fed, ECB, BoE, etc.) | `fetch_cb_forecasts.py` (TO BUILD) |

### JavaScript Architecture

**`country.js`** should contain:
- Country metadata (names, flags, targets) — OK to hardcode, rarely changes
- Target descriptions and quotes — OK to hardcode, rarely changes
- Data source links — OK to hardcode, rarely changes
- **Functions that LOAD data from JSON files** — NOT hardcoded values

**`index.js`** (or inline in `index.html`) should:
- Load data from JSON files
- Dynamically render the overview table
- Dynamically render the Central Bank Outlook table

---

## Data Flow

### Current (Broken) Flow
```
┌─────────────────────────────────────────────────────────┐
│ fetch_historical_cpi.py → historical_cpi.json          │
│                                    ↓                    │
│                           country.js reads this ✅      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ fetch_imf_forecasts.py → imf_forecasts.json            │
│                                    ↓                    │
│                           country.js reads this ✅      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Central Bank Forecasts:                                 │
│   - index.html has HARDCODED values (Dec 2025) ❌      │
│   - country.js has DIFFERENT hardcoded values (2024) ❌│
│   - NO JSON file, NO script to fetch ❌                │
└─────────────────────────────────────────────────────────┘
```

### Target Flow
```
┌─────────────────────────────────────────────────────────┐
│                    Python Scripts                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────┐ │
│  │fetch_historical_│ │fetch_imf_       │ │fetch_cb_  │ │
│  │cpi.py           │ │forecasts.py     │ │forecasts.py│ │
│  └────────┬────────┘ └────────┬────────┘ └─────┬─────┘ │
└───────────┼────────────────────┼────────────────┼───────┘
            ↓                    ↓                ↓
┌───────────┴────────────────────┴────────────────┴───────┐
│                    docs/data/                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────┐ │
│  │historical_cpi.  │ │imf_forecasts.   │ │cb_forecasts│ │
│  │json             │ │json             │ │.json      │ │
│  └────────┬────────┘ └────────┬────────┘ └─────┬─────┘ │
└───────────┼────────────────────┼────────────────┼───────┘
            ↓                    ↓                ↓
┌───────────┴────────────────────┴────────────────┴───────┐
│                    Web Pages                             │
│  ┌─────────────────┐ ┌─────────────────────────────────┐│
│  │index.html       │ │us.html, uk.html, ea.html, ...  ││
│  │(loads all JSON) │ │(load via country.js)           ││
│  └─────────────────┘ └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

### Target Structure
```
inflation-dashboard/
├── README.md                    # Project overview (NEEDS UPDATE)
├── METHODOLOGY.md               # Technical documentation
├── PROJECT_PLAN.md              # This file
├── scripts/
│   ├── fetch_historical_cpi.py  # ✅ Exists - fetches CPI from FRED
│   ├── fetch_imf_forecasts.py   # ✅ Exists - fetches IMF WEO
│   └── fetch_cb_forecasts.py    # ❌ TO BUILD - central bank forecasts
├── data/                        # Raw output from scripts
│   ├── historical_cpi.json
│   ├── imf_forecasts.json
│   └── cb_forecasts.json        # ❌ TO BUILD
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview page
│   ├── us.html                  # Country pages
│   ├── uk.html
│   ├── ea.html
│   ├── au.html
│   ├── ca.html
│   ├── nz.html
│   ├── za.html
│   ├── cn.html
│   ├── styles.css               # Shared styles
│   ├── country.js               # Shared JS for country pages
│   └── data/                    # Data files served to browser
│       ├── historical_cpi.json
│       ├── imf_forecasts.json
│       └── cb_forecasts.json    # ❌ TO BUILD
└── .github/
    └── workflows/
        └── update-data.yml      # ❓ Check if exists - weekly automation
```

---

## Scripts & Automation

### `fetch_historical_cpi.py`
- **Status:** ✅ Exists and works
- **Function:** Fetches 10-year CPI data from FRED API
- **Output:** `data/historical_cpi.json`
- **Requires:** `FRED_API_KEY` environment variable

### `fetch_imf_forecasts.py`
- **Status:** ✅ Exists and works
- **Function:** Fetches IMF World Economic Outlook inflation projections
- **Output:** `data/imf_forecasts.json`
- **Requires:** No API key (public API)

### `fetch_cb_forecasts.py`
- **Status:** ❌ Needs to be built or recovered
- **Function:** Fetches/scrapes central bank forecasts
- **Output:** `data/cb_forecasts.json`
- **Sources:**
  - US: FOMC SEP (Summary of Economic Projections)
  - EA: ECB Staff Projections
  - UK: BoE Monetary Policy Report
  - AU: RBA Statement on Monetary Policy
  - CA: BoC Monetary Policy Report
  - NZ: RBNZ Monetary Policy Statement
  - ZA: SARB MPC Statement
  - CN: IMF (China doesn't publish multi-year forecasts)

### GitHub Actions Workflow
- **Status:** ❓ Check if exists at `.github/workflows/update-data.yml`
- **Function:** Runs scripts weekly, commits updated JSON files
- **Schedule:** Weekly (e.g., every Monday)

---

## Known Issues & Fixes Needed

### Issue 1: Hardcoded Forecasts in index.html
**Problem:** The Central Bank Outlook table in `index.html` has forecasts hardcoded directly in the HTML (e.g., "FOMC Dec '25", "2.8%", "2.4%", "2.1%").

**Fix:** 
1. Create `cb_forecasts.json` with structured forecast data
2. Modify `index.html` to load and render from JSON
3. Remove hardcoded values

### Issue 2: Outdated Forecasts in country.js
**Problem:** The `FORECASTS` object in `country.js` has 2024 data while `index.html` has 2025 data.

**Fix:** 
1. Either update `country.js` manually to match, OR
2. (Better) Have `country.js` load from `cb_forecasts.json` instead of hardcoding

### Issue 3: README.md Outdated
**Problem:** README doesn't reflect current architecture or country coverage.

**Fix:** Deploy the updated README (created in this session but failed to commit due to identical content issue).

### Issue 4: No Automation for CB Forecasts
**Problem:** Central bank forecasts require manual updates.

**Fix:** Build `fetch_cb_forecasts.py` that either:
- Scrapes central bank websites, or
- Provides a structured way to manually update with validation

---

## Priority List

### P0 — Critical (Data Accuracy & Consistency)
| Task | Description | Status |
|------|-------------|--------|
| Fix data inconsistency | All pages read from same JSON sources | ❌ |
| Update CB forecasts | Match country.js to index.html (2025 data) | ❌ |
| Create cb_forecasts.json | Single source for CB forecast data | ❌ |
| Update README.md | Document current architecture | ❌ |

### P1 — Important (Automation)
| Task | Description | Status |
|------|-------------|--------|
| Build fetch_cb_forecasts.py | Script to update CB forecasts | ❌ |
| Verify GitHub Actions | Ensure weekly updates work | ❓ |
| index.html dynamic loading | Load forecast table from JSON | ❌ |

### P2 — Enhancements
| Task | Description | Status |
|------|-------------|--------|
| Add more countries | Japan, Singapore, India, etc. | ❌ |
| Email subscription | Alerts for material changes | ❌ |
| Supabase backend | Store forecast history | ❌ |

---

## Session Recovery Guide

If starting a new session or recovering from a crash, use this checklist:

### 1. Check Current State
```bash
cd ~/Projects/inflation-dashboard

# What branch are we on?
git branch

# What's the latest commit?
git log --oneline -5

# What files exist?
ls -la docs/
ls -la docs/data/
ls -la scripts/
ls -la .github/workflows/
```

### 2. Check Data Freshness
```bash
# When was CPI data last updated?
head -20 docs/data/historical_cpi.json

# When was IMF data last updated?
head -20 docs/data/imf_forecasts.json
```

### 3. Check for Inconsistencies
```bash
# What forecasts are in index.html?
grep -A 5 "FOMC" docs/index.html | head -10

# What forecasts are in country.js?
grep -A 10 "US:" docs/country.js | head -15
```

### 4. Test the Site
- Open https://jing-ny.github.io/inflation-dashboard/
- Check overview table loads
- Check Central Bank Outlook table
- Click into a country page (e.g., us.html)
- Verify forecast table shows

### 5. Reference This Document
- This file should be at `PROJECT_PLAN.md` in repo root
- Contains architecture, known issues, and fix priorities

---

## Git History Reference

Key commits to know about:

| Commit | Description | State |
|--------|-------------|-------|
| `00d7bfa` | "Add central bank outlook to overview, update all forecasts" | ✅ Working overview with forecasts |
| `c3d0211` | "v2.0: Dynamic architecture + updated docs" | ❌ Broke things (simplified too much) |

If things break badly, can revert to `00d7bfa`:
```bash
git reset --hard 00d7bfa
git push --force origin main
```

---

## README Template

**IMPORTANT:** This is the original README style that Jo likes. Use this template when updating README.md — keep the tone and structure, just update the details.

```markdown
# Inflation, Officially

**Official Data & Central Bank Expectations**

A lightweight, source-first monitor of inflation trends and central bank expectations across major economies.

---

## Why This Exists

Inflation data is everywhere, but it is often difficult to interpret in a consistent way.  
Figures are reported using different definitions, released on different schedules, and frequently mixed with commentary or opinion.

This project exists to cut through that noise.

It aggregates official inflation statistics and central bank projections in one place, with clear source attribution for every number, making cross-country comparison easier and more transparent.

---

## What This Project Does (and Does Not Do)

**What this project does:**

- Collects headline CPI inflation data from official government statistics agencies
- Displays central bank inflation expectations and projections where available
- Compares central bank forecasts with IMF World Economic Outlook projections
- Provides direct source links for every data point

**What this project does not do:**

- Provide analysis or commentary
- Make predictions
- Offer investment advice or policy recommendations

---

## Coverage

This dashboard tracks headline consumer price inflation (year-over-year) across 8 major economies:

| Economy | Inflation Measure | Source | Central Bank |
|---------|-------------------|--------|--------------|
| United States | CPI (YoY) | Bureau of Labor Statistics | Federal Reserve |
| Euro Area | HICP (YoY) | Eurostat | ECB |
| United Kingdom | CPI (YoY) | ONS | Bank of England |
| Australia | CPI (YoY) | ABS | RBA |
| Canada | CPI (YoY) | Statistics Canada | Bank of Canada |
| New Zealand | CPI (YoY) | Stats NZ | RBNZ |
| South Africa | CPI (YoY) | Stats SA | SARB |
| China | CPI (YoY) | NBS | PBOC |

---

## Data Sources and Methodology

All data comes directly from official government statistics agencies or central bank publications.

Data sources are not forced into a single uniform pipeline.  
Instead, each economy uses the most stable and authoritative official source available.  
This approach prioritizes **stability and reproducibility** over uniformity.

Every figure displayed can be traced back to its original source.

For detailed methodology, see [METHODOLOGY.md](METHODOLOGY.md).

---

## Update Frequency

- **CPI Data:** Updated weekly, reflecting the most recent official releases
- **Central Bank Forecasts:** Updated after major monetary policy meetings
- **IMF Forecasts:** Updated twice yearly (April and October WEO releases)

Values may be revised by the original statistical agencies after publication.

---

## Disclaimer

This project is provided for informational purposes only.

It does not offer analysis, predictions, investment advice, or policy recommendations.  
Users should refer to the original sources for official data and methodological details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
```

**Key principles of this README style:**
1. Clean, minimal formatting
2. Clear "what it does / doesn't do" section
3. Source-first philosophy emphasized
4. No hype, no predictions, just facts
5. Disclaimer at the end

---

## Contact & Notes

**Owner:** Jo (jing-ny on GitHub)  
**Location:** Greenwich, Connecticut, US  

**Key Decisions Made:**
1. Keep individual country HTML files (us.html, uk.html, etc.) rather than single dynamic page
2. Use FRED API as primary CPI data source
3. Include IMF WEO forecasts alongside central bank forecasts
4. Focus on 8 major economies (removed Japan, Germany, Switzerland due to data issues)

---

*This document should be updated whenever significant architectural changes are made.*
