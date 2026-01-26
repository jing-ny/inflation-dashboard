# Inflation Dashboard - Project Plan & Architecture

**Last Updated:** January 26, 2026  
**Purpose:** Reference document to maintain consistency across sessions and recover from any disruptions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [Architecture](#architecture)
4. [Data Flow](#data-flow)
5. [File Structure](#file-structure)
6. [Scripts & Automation](#scripts--automation)
7. [Data Sources & Known Limitations](#data-sources--known-limitations)
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
| CA | Canada | Statistics Canada | Bank of Canada | Monthly |
| AU | Australia | ABS | RBA | Monthly (new) / Quarterly (historical) |
| NZ | New Zealand | Stats NZ | RBNZ | Quarterly |
| ZA | South Africa | Stats SA | SARB | Monthly |
| CN | China | NBS | PBOC | Monthly |

---

## Current State (as of Jan 26, 2026)

### ✅ What Works
- Overview page (`index.html`) with summary table and Central Bank Outlook
- Individual country pages (us.html, uk.html, ea.html, ca.html, au.html, nz.html, za.html, cn.html)
- All pages load CPI data from `data/historical_cpi.json`
- All pages load CB forecasts from `data/cb_forecasts.json`
- All pages load IMF forecasts from `data/imf_forecasts.json`
- `fetch_historical_cpi.py` fetches CPI from FRED API
- `fetch_imf_forecasts.py` fetches IMF WEO projections
- `fetch_cb_forecasts.py` with hybrid API + manual data approach
- GitHub Actions workflow for weekly automated updates
- CPI supplements system for countries where FRED lags official releases

### ⚠️ Known Limitations
- **FRED data lag:** Some countries (especially ZA, UK, CA) have FRED data that lags official releases
- **Solution:** `cpi_supplements.json` provides manual overrides; `historical_cpi.json` updated directly
- **CB forecasts:** Most require manual updates after monetary policy meetings
- **AU transition:** Australia moved from quarterly to monthly CPI in Oct 2025

---

## Architecture

### Core Principle: Single Source of Truth

All data flows from JSON files that are updated by Python scripts:

```
Python Scripts (fetch/update data)
        ↓
    JSON Files (single source of truth)
        ↓
    HTML/JS Pages (read and display)
```

### Data Files (in `docs/data/`)

| File | Contents | Updated By |
|------|----------|------------|
| `historical_cpi.json` | 10-year CPI history + latest/previous readings | `fetch_historical_cpi.py` + manual supplements |
| `imf_forecasts.json` | IMF WEO inflation projections | `fetch_imf_forecasts.py` |
| `cb_forecasts.json` | Central bank forecasts | `fetch_cb_forecasts.py` (hybrid) |

### JavaScript Architecture

**`country.js`** contains:
- Country metadata (names, flags, targets) — hardcoded, rarely changes
- Target descriptions and policy quotes — hardcoded
- Data source links — hardcoded
- Functions that LOAD data from JSON files — dynamic

**`index.html`** contains:
- Inline JS that loads all JSON files
- Dynamically renders overview table
- Dynamically renders Central Bank Outlook table

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python Scripts                                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │fetch_historical_│ │fetch_imf_       │ │fetch_cb_        │   │
│  │cpi.py           │ │forecasts.py     │ │forecasts.py     │   │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘   │
└───────────┼────────────────────┼────────────────────┼───────────┘
            ↓                    ↓                    ↓
┌───────────┴────────────────────┴────────────────────┴───────────┐
│                    docs/data/                                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │historical_cpi.  │ │imf_forecasts.   │ │cb_forecasts.    │   │
│  │json             │ │json             │ │json             │   │
│  └────────┬────────┘ └────────┬────────┘ └────────┬────────┘   │
└───────────┼────────────────────┼────────────────────┼───────────┘
            ↓                    ↓                    ↓
┌───────────┴────────────────────┴────────────────────┴───────────┐
│                    Web Pages                                     │
│  ┌─────────────────┐ ┌──────────────────────────────────────┐  │
│  │index.html       │ │us.html, uk.html, ea.html, ca.html,   │  │
│  │(overview)       │ │au.html, nz.html, za.html, cn.html    │  │
│  └─────────────────┘ └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
inflation-dashboard/
├── README.md                    # Project overview (user-facing)
├── METHODOLOGY.md               # Technical documentation
├── PROJECT_PLAN.md              # This file (internal reference)
├── scripts/
│   ├── fetch_historical_cpi.py  # ✅ Fetches CPI from FRED
│   ├── fetch_imf_forecasts.py   # ✅ Fetches IMF WEO
│   └── fetch_cb_forecasts.py    # ✅ Hybrid API + manual CB forecasts
├── data/
│   ├── historical_cpi.json      # CPI data (source for docs/)
│   ├── imf_forecasts.json       # IMF data (source for docs/)
│   ├── cb_forecasts.json        # CB forecasts (source for docs/)
│   └── cpi_supplements.json     # Manual supplements for FRED lag
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview page
│   ├── us.html, uk.html, ...    # Country pages (8 total)
│   ├── styles.css               # Shared styles
│   ├── country.js               # Shared JS for country pages
│   └── data/                    # Data files served to browser
│       ├── historical_cpi.json
│       ├── imf_forecasts.json
│       └── cb_forecasts.json
└── .github/
    └── workflows/
        └── update-data.yml      # ✅ Weekly automation
```

---

## Scripts & Automation

### `fetch_historical_cpi.py`
- **Status:** ✅ Working
- **Function:** Fetches 10-year CPI data from FRED API for all countries
- **Output:** `data/historical_cpi.json`
- **Requires:** `FRED_API_KEY` environment variable
- **Note:** FRED data lags for some countries; use supplements

### `fetch_imf_forecasts.py`
- **Status:** ✅ Working
- **Function:** Fetches IMF World Economic Outlook inflation projections
- **Output:** `data/imf_forecasts.json`
- **Requires:** No API key (public API)

### `fetch_cb_forecasts.py`
- **Status:** ✅ Working (hybrid approach)
- **Function:** Fetches Fed/Cleveland Fed from FRED API; other CBs from manual data
- **Output:** `data/cb_forecasts.json`
- **Sources:**
  - US Fed: FRED API (PCECTPIMD series)
  - Cleveland Fed: FRED API (EXPINF1YR series)
  - ECB, BoE, RBA, BoC, RBNZ, SARB: Manual data in script

### GitHub Actions Workflow
- **Status:** ✅ Configured
- **Location:** `.github/workflows/update-data.yml`
- **Schedule:** Weekly (Mondays at 9 AM UTC)
- **Function:** Runs all fetch scripts, copies to docs/data/, commits changes

---

## Data Sources & Known Limitations

### FRED API Data Lag Issue

FRED OECD series for international countries often lag official releases:

| Country | FRED Series | Typical Lag | Solution |
|---------|-------------|-------------|----------|
| ZA | ZAFCPIALLMINMEI | 6-12 months | Manual supplement from Stats SA |
| UK | GBRCPIALLMINMEI | 1-2 months | Manual supplement from ONS |
| CA | CANCPIALLMINMEI | 1-2 months | Manual supplement from StatCan |
| AU | AUSCPIALLQINMEI | 1-2 quarters | New monthly series available |
| NZ | NZLCPIALLQINMEI | 1-2 quarters | Quarterly only (no monthly) |

**Workaround:** 
1. `cpi_supplements.json` stores manual data for lagging countries
2. After running `fetch_historical_cpi.py`, manually update or run patch script
3. Alternatively, directly update `historical_cpi.json` with latest official data

### Central Bank Forecast Update Schedule

| Bank | Forecast Release | Frequency |
|------|------------------|-----------|
| Fed (FOMC) | Summary of Economic Projections | 4x/year (Mar, Jun, Sep, Dec) |
| Cleveland Fed | Inflation Expectations | Monthly |
| ECB | Staff Projections | 4x/year (Mar, Jun, Sep, Dec) |
| BoE | Monetary Policy Report | 4x/year (Feb, May, Aug, Nov) |
| RBA | Statement on Monetary Policy | 4x/year |
| BoC | Monetary Policy Report | 4x/year (Jan, Apr, Jul, Oct) |
| RBNZ | Monetary Policy Statement | 7x/year |
| SARB | MPC Statement | 6x/year |

---

## Priority List

### ✅ Completed (P0/P1)
| Task | Description | Status |
|------|-------------|--------|
| Single source of truth | All pages read from JSON | ✅ |
| CB forecasts JSON | cb_forecasts.json with all banks | ✅ |
| IMF forecasts | imf_forecasts.json working | ✅ |
| GitHub Actions | Weekly automation configured | ✅ |
| Fix ZA data lag | Manual supplement system | ✅ |
| Fix UK/CA data lag | Updated historical_cpi.json | ✅ |

### 🔄 Ongoing Maintenance
| Task | Description | Frequency |
|------|-------------|-----------|
| Update CPI supplements | When FRED lags official releases | As needed |
| Update CB forecasts | After monetary policy meetings | ~Monthly |
| Update IMF forecasts | After WEO releases | 2x/year |

### 📋 Future Enhancements (P2)
| Task | Description | Priority |
|------|-------------|----------|
| Auto-scrape CB forecasts | Replace manual data entry | Medium |
| Add more countries | Japan, India, Singapore | Low |
| Email alerts | Notify on significant changes | Low |
| Historical forecast tracking | Store past forecasts | Low |

---

## Session Recovery Guide

If starting a new session or recovering from a crash:

### 1. Check Current State
```bash
cd ~/Projects/inflation-dashboard

# What branch are we on?
git branch

# What's the latest commit?
git log --oneline -5

# What files exist?
ls -la docs/data/
ls -la scripts/
```

### 2. Check Data Freshness
```bash
# Check CPI data date
head -5 docs/data/historical_cpi.json

# Check CB forecasts date
head -10 docs/data/cb_forecasts.json
```

### 3. Test the Site
- Open https://jing-ny.github.io/inflation-dashboard/
- Check overview table loads with current data
- Check Central Bank Outlook table
- Click into country pages, verify data matches

### 4. Common Issues
- **Stale data:** Run fetch scripts or manually update JSON
- **FRED lag:** Use cpi_supplements.json approach
- **Page not updating:** Check GitHub Pages deployment status

---

## README Template

**IMPORTANT:** This is the original README style that Jing likes. Use this template when updating README.md — keep the tone and structure, just update the details.

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
| Canada | CPI (YoY) | Statistics Canada | Bank of Canada |
| Australia | CPI (YoY) | ABS | RBA |
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
```

**Key principles:**
1. Clean, minimal formatting
2. Clear "what it does / doesn't do" section
3. Source-first philosophy emphasized
4. No hype, no predictions, just facts
5. Disclaimer at the end

---

*This document should be updated whenever significant architectural changes are made.*
