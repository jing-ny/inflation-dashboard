# Inflation Dashboard - Project Plan & Architecture

**Last Updated:** January 27, 2026  
**Purpose:** Reference document to maintain consistency across sessions and recover from any disruptions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [Open Issues](#open-issues)
4. [Architecture](#architecture)
5. [Data Flow](#data-flow)
6. [File Structure](#file-structure)
7. [Automation](#automation)
8. [Manual Maintenance Tasks](#manual-maintenance-tasks)
9. [Data Sources & Known Limitations](#data-sources--known-limitations)
10. [Session Recovery Guide](#session-recovery-guide)

---

## Project Overview

**Name:** Inflation, Officially  
**URL:** https://jing-ny.github.io/inflation-dashboard/  
**Repo:** https://github.com/jing-ny/inflation-dashboard  

**Purpose:** A source-first dashboard tracking official CPI inflation data and central bank forecasts across 13 economies.

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
| JP | Japan | Statistics Bureau | Bank of Japan | Monthly |
| KR | South Korea | KOSTAT | Bank of Korea | Monthly |
| SG | Singapore | DOS | MAS | Monthly |
| IN | India | MOSPI | RBI | Monthly |
| CN | China | NBS | PBOC | Monthly |
| VE | Venezuela | BCV | BCV | Monthly |

---

## Current State (as of Jan 27, 2026)

### ✅ What Works
- Overview page (`index.html`) with summary table and Central Bank Outlook
- Individual country pages (13 total)
- All pages load data from JSON files (single source of truth)
- GitHub Actions automation runs Mon & Thu at 9am UTC
- Email notifications via Resend (delivery issues - see Open Issues)
- Forecast history tracking system

### ⚠️ Recent Changes
- **Jan 27, 2026:** Added Japan, India, South Korea, Singapore, Venezuela (5 new countries)
- **Jan 27, 2026:** South Africa target updated from 4.5% to 3% (±1pp)
- **Jan 27, 2026:** Venezuela null target handling fixed
- **Jan 27, 2026:** Automation system deployed with Resend email

---

## Open Issues

### 🔴 Active Issues

#### 1. Email notifications not arriving
- **Status:** Resend shows "Delivered" but emails not received in inbox
- **To investigate:**
  - Check Resend "To" field for correct recipient
  - Check spam/junk folder
  - Verify `NOTIFICATION_EMAIL` GitHub secret
  - Consider switching from `@resend.dev` to verified domain
- **Workaround:** Check Resend dashboard directly for notification content

#### 2. FRED API errors for Japan & Singapore
- **Error:** `400 Bad Request` for series JPNCPALTT01GYM659N and SGPCPIALLMINMEI
- **Cause:** These series don't support `units=pc1` parameter
- **Impact:** Low - dashboard still works, just can't auto-update these countries
- **Fix needed:** Update `monitor_updates.py` to handle these series differently

#### 3. Venezuela data stale (301 days)
- **Status:** Expected - FRED doesn't update VE frequently
- **Impact:** Low - VE page works, just shows older data
- **Fix:** Manual update from BCV/IMF sources when available

### ✅ Recently Fixed

- **Venezuela page "Error loading data"** (Jan 27): Fixed null target handling in country.js
- **Quarterly date format crash** (Jan 27): Fixed AU/NZ `2025-Q4` format in monitor script

### 📋 Future Enhancements (Low Priority)

- Auto-scrape CB forecasts from official websites
- Forecast revision visualization on country pages
- Historical forecast accuracy charts
- Fix FRED API errors for JP/SG series

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
| `historical_cpi.json` | 10-year CPI history + latest/previous readings | Automation + manual |
| `imf_forecasts.json` | IMF WEO inflation projections | Manual (2x/year) |
| `cb_forecasts.json` | Central bank forecasts | Manual (after MPC meetings) |
| `history/cb_forecast_history.json` | CB forecast snapshots | Manual (optional) |
| `history/imf_forecast_history.json` | IMF forecast snapshots | Manual (optional) |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Automation (GitHub Actions)                   │
│  ┌─────────────────┐ ┌─────────────────┐                        │
│  │monitor_updates. │ │send_notification│                        │
│  │py               │ │.py (Resend)     │                        │
│  └────────┬────────┘ └────────┬────────┘                        │
└───────────┼────────────────────┼────────────────────────────────┘
            ↓                    ↓
┌───────────┴────────────────────┴────────────────────────────────┐
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
│  │index.html       │ │us.html, uk.html, ... ve.html         │  │
│  │(overview)       │ │(13 country pages)                    │  │
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
├── MAINTENANCE.md               # Manual update guide
├── scripts/
│   ├── monitor_updates.py       # ✅ Checks FRED for new data
│   └── send_notification.py     # ✅ Sends email via Resend
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview page
│   ├── *.html                   # Country pages (13 total)
│   ├── styles.css               # Shared styles
│   ├── country.js               # Shared JS for country pages
│   └── data/                    # Data files served to browser
│       ├── historical_cpi.json
│       ├── imf_forecasts.json
│       ├── cb_forecasts.json
│       └── history/             # Forecast revision tracking
└── .github/
    └── workflows/
        └── monitor-updates.yml  # ✅ Twice-weekly automation
```

---

## Automation

### GitHub Actions Workflow

**File:** `.github/workflows/monitor-updates.yml`  
**Schedule:** Monday & Thursday at 9 AM UTC  
**Manual trigger:** GitHub repo → Actions → Run workflow

**What it does:**
1. Checks FRED API for new CPI data for all 13 countries
2. If new data found → auto-commits to repo
3. Checks for stale data (>75 days old) → alerts
4. Checks CB meeting schedule → alerts if forecasts may need updating
5. Checks if IMF WEO month (Apr/Oct) → alerts
6. Sends email summary via Resend

### GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `FRED_API_KEY` | FRED API access |
| `RESEND_API_KEY` | Email notifications |
| `NOTIFICATION_EMAIL` | Recipient email |

### What's Automated vs Manual

| Task | Automated | Manual |
|------|-----------|--------|
| CPI data updates | ✅ (FRED fetch) | Supplement if FRED lags |
| Stale data alerts | ✅ | — |
| CB meeting reminders | ✅ | Update forecasts |
| IMF WEO reminders | ✅ | Update forecasts |
| CB forecast updates | — | After MPC meetings |
| IMF forecast updates | — | April & October |

---

## Manual Maintenance Tasks

### Central Bank Forecast Updates

**When:** After major MPC meetings (varies by country)  
**What:** Edit `docs/data/cb_forecasts.json`  
**Key meetings:**
- US FOMC: Mar, Jun, Sep, Dec
- ECB: Mar, Jun, Sep, Dec
- BoE: Feb, May, Aug, Nov
- Others: See MAINTENANCE.md

### IMF Forecast Updates

**When:** April and October (WEO releases)  
**What:** Edit `docs/data/imf_forecasts.json`  
**Source:** https://www.imf.org/external/datamapper/PCPIPCH@WEO

### Full Details

See `MAINTENANCE.md` for step-by-step instructions.

---

## Data Sources & Known Limitations

### FRED API Data Lag Issue

FRED OECD series for international countries often lag official releases:

| Country | FRED Series | Typical Lag | Solution |
|---------|-------------|-------------|----------|
| ZA | ZAFCPIALLMINMEI | 6-12 months | Manual supplement from Stats SA |
| UK | GBRCPIALLMINMEI | 1-2 months | Manual supplement from ONS |
| CA | CANCPIALLMINMEI | 1-2 months | Manual supplement from StatCan |
| AU | AUSCPIALLQINMEI | 1-2 quarters | Quarterly data |
| NZ | NZLCPIALLQINMEI | 1-2 quarters | Quarterly only |
| VE | FPCPITOTLZGVEN | 6-12 months | IMF data preferred |

### FRED API Compatibility Issues

| Country | Series | Issue |
|---------|--------|-------|
| JP | JPNCPALTT01GYM659N | Doesn't support `units=pc1` |
| SG | SGPCPIALLMINMEI | Doesn't support `units=pc1` |

### Special Cases

- **Venezuela:** No inflation target; `target: null` in data files
- **Singapore:** MAS uses exchange rate policy, not interest rates
- **Australia:** Transitioned from quarterly to monthly CPI in Oct 2025

---

## Session Recovery Guide

If starting a new session or recovering from a crash:

### 1. Check Current State
```bash
cd ~/Projects/inflation-dashboard

# What's the latest commit?
git log --oneline -5

# What files exist?
ls -la docs/data/
```

### 2. Check Data Freshness
```bash
# Check last update date
head -5 docs/data/historical_cpi.json
```

### 3. Test the Site
- Open https://jing-ny.github.io/inflation-dashboard/
- Check overview table loads
- Click Venezuela page (tests null target handling)

### 4. Check Automation
- GitHub repo → Actions tab
- Check latest workflow run status
- Check Resend dashboard for email delivery

---

## Useful Links

- **Dashboard:** https://jing-ny.github.io/inflation-dashboard/
- **GitHub repo:** https://github.com/jing-ny/inflation-dashboard
- **Actions:** https://github.com/jing-ny/inflation-dashboard/actions
- **Resend:** https://resend.com/emails
- **FRED:** https://fred.stlouisfed.org/
- **IMF DataMapper:** https://www.imf.org/external/datamapper/PCPIPCH@WEO

---

*This document should be updated whenever significant architectural changes are made.*
