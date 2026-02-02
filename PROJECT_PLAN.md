# Inflation Dashboard - Project Plan & Architecture

**Last Updated:** February 2, 2026  
**Purpose:** Reference document to maintain consistency across sessions and recover from any disruptions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [To-Do List](#to-do-list)
4. [Open Issues](#open-issues)
5. [Architecture](#architecture)
6. [Data Flow](#data-flow)
7. [File Structure](#file-structure)
8. [Automation](#automation)
9. [Manual Maintenance Tasks](#manual-maintenance-tasks)
10. [Data Sources & Known Limitations](#data-sources--known-limitations)
11. [Session Recovery Guide](#session-recovery-guide)

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

## Current State (as of Feb 2, 2026)

### ✅ What Works (locally)
- Overview page (`index.html`) with summary table, Central Bank Outlook, and Policy Rates grid
- Individual country pages (13 total), all loading data dynamically from JSON
- Shared `country.js` module for all country pages (single source of truth)
- CPI data in `historical_cpi.json` current through Dec 2025 for most countries
- CB forecasts in `cb_forecasts.json` populated for all 13 countries
- IMF forecasts from Oct 2025 WEO for all 13 countries
- Newsletter signup via Substack embed on homepage
- 5 GitHub Actions workflows defined
- Email notification scripts using Resend API

### 🔴 Critical Problem: Live Site Out of Sync
- GitHub repo has only **2 commits** and an outdated MVP README (3 countries, Supabase/Vercel)
- The live site at jing-ny.github.io shows only **8 countries** with stale CPI dates (some from Jan-Apr 2025)
- The local codebase has evolved far beyond what's deployed
- **First priority: push all local changes to GitHub**

### ⚠️ Recent Changes (local, not yet deployed)
- **Jan 27, 2026:** Added Japan, India, South Korea, Singapore, Venezuela (5 new countries)
- **Jan 27, 2026:** South Africa target updated from 4.5% to 3% (±1pp)
- **Jan 27, 2026:** Venezuela null target handling fixed
- **Jan 27, 2026:** Automation system deployed with Resend email

---

## To-Do List

### 🔴 Phase 0: Deploy What You Have

| # | Task | Details | Status |
|---|------|---------|--------|
| 0.1 | Push local codebase to GitHub | `git add -A && git commit && git push` — the live site is way behind | ⬜ |
| 0.2 | Update repo README | Still says "MVP, 3 countries, Supabase/Vercel" — needs to reflect actual state | ⬜ |
| 0.3 | Verify GitHub Pages config | Confirm Pages source is set to `main` branch, `/docs` folder | ⬜ |
| 0.4 | Add repo description & topics | Currently "No description, website, or topics provided" on GitHub | ⬜ |

### 🟠 Phase 1: Data Freshness

#### 1.1 Central Bank Forecast & Rate Updates

Several CB meetings have occurred since the data was last updated. These need to be reflected in `docs/data/cb_forecasts.json`.

| Country | Data From | What's Missed | Priority |
|---------|-----------|---------------|----------|
| 🇨🇦 Canada (BoC) | Oct 2025 | Dec 2025 rate cut + **Jan 29 MPR** (full new projections) | 🔴 Critical — 3+ months stale |
| 🇬🇧 UK (BoE) | Nov 2025 | Dec 18 rate decision + **Feb 5 MPR** (full projections, 3 days away) | 🔴 Critical |
| 🇿🇦 South Africa (SARB) | Nov 2025 | **Jan 29-30 MPC** meeting (rate + projections) | 🔴 Critical |
| 🇦🇺 Australia (RBA) | Nov 2025 | Dec 9-10 rate decision; Feb 17-18 SoMP upcoming | 🟡 Rate only for now |
| 🇰🇷 South Korea (BOK) | Nov 2025 | Jan 16 rate decision | 🟡 Rate only |
| 🇺🇸 US (Fed) | Dec 2025 | Jan 28-29 FOMC (no SEP, rate decision only) | 🟡 Rate only |
| 🇪🇺 Euro Area (ECB) | Dec 2025 | Jan 30 meeting (rate decision only) | 🟡 Rate only |
| 🇯🇵 Japan (BoJ) | Jan 2026 | Current — Jan Outlook Report already in data | ✅ OK |
| 🇮🇳 India (RBI) | Dec 2025 | Feb 5-7 meeting upcoming | ✅ OK for now |
| 🇳🇿 New Zealand (RBNZ) | Nov 2025 | Feb 19 MPS upcoming | ✅ OK for now |

#### 1.2 CPI Data Gaps

| Country | Latest in Data | Expected | Issue |
|---------|---------------|----------|-------|
| VE | 2025-04 | Unknown | 🔴 10 months stale — BCV publishes irregularly. Search for newer data. |
| KR | 2025-12 | 2026-01? | 🟡 Jan 2026 CPI may already be published. Check. |
| All others | 2025-12 or 2025-Q4 | 2025-12 / Q4 | ✅ Current |

#### 1.3 Upcoming Meetings to Watch (Feb 2026)

| Date | Bank | Type | Action Needed |
|------|------|------|---------------|
| Feb 5 | BoE | MPR (full projections) | Update forecasts + rate |
| Feb 5-7 | RBI | MPC meeting | Check for rate change |
| Feb 17-18 | RBA | SoMP (full projections) | Update forecasts + rate |
| Feb 19 | RBNZ | MPS (full projections) | Update forecasts + rate |
| Feb 27 | BOK | Rate decision | Check for rate change |

### 🟡 Phase 2: Automation & Accuracy

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.1 | Add 5 missing countries to `fetch_historical_cpi.py` | JP, IN, KR, SG, VE are NOT in the FRED fetch script. Their CPI data won't auto-update. Need FRED series IDs or alternative fetch logic. | ⬜ |
| 2.2 | Expand auto-scraper to more central banks | `auto_scrape_cb_forecasts.py` only covers ECB, BoE, RBA, BoC, RBNZ, SARB (6 of 13). Missing: Fed, BoJ, BOK, MAS, RBI, PBoC. Need scrapers or calendar-based reminders. | ⬜ |
| 2.3 | Fix scraper output format mismatch | Auto-scraper writes draft JSON with flat list structure but actual `cb_forecasts.json` uses keyed-by-country-code format. `compare_forecasts()` won't work correctly. Needs reconciliation. | ⬜ |
| 2.4 | Switch workflows from direct commits to PRs | `update-data.yml` and `monitor-updates.yml` commit directly to main. Should create PRs for human review. | ⬜ |
| 2.5 | Wire up weekly alert workflow | `weekly-alert.yml` is a stub — just prints data. The real logic in `send_weekly_alert.py` (612 lines) is never called by the workflow. | ⬜ |
| 2.6 | Fix Resend email delivery | Emails show "Delivered" in Resend dashboard but aren't reaching inbox. Investigate SPF/DKIM, spam filters, `from` address config. | ⬜ |
| 2.7 | Make `index.html` year columns dynamic | Central Bank Outlook table headers hardcoded as 2025/2026/2027. Should update as calendar year changes. | ⬜ |
| 2.8 | Expand `cpi_supplements.json` | Only covers UK, CA, AU, NZ, ZA. No supplement mechanism for JP, IN, KR, SG, VE when FRED lags. | ⬜ |

### 🟢 Phase 3: Newsletter & Engagement

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.1 | Define quarterly newsletter pipeline | Site promises "~6 emails/year" but no process exists. Need to decide: what triggers a send, what content goes in, manual vs automated. | ⬜ |
| 3.2 | Wire up weekly alert emails | Connect `send_weekly_alert.py` to the GitHub Actions workflow. Define "material change" thresholds (currently spec'd as ≥0.3pp). | ⬜ |
| 3.3 | Decide newsletter platform | Substack embed is live. Decide if Substack is the long-term home or if direct Resend sends are better. | ⬜ |

### 🔵 Phase 4: Housekeeping & Polish

| # | Task | Details | Status |
|---|------|---------|--------|
| 4.1 | Update CHANGELOG | Still says "9 countries" in v1.0.0. Roadmap lists countries already added (SG, IN). Missing entries for KR, SG, IN, VE. | ⬜ |
| 4.2 | Clean up legacy files | Root `data/` has per-country JSONs (`us_cpi.json`, `ch_cpi.json`, `de_cpi.json`) from pre-consolidation. Also legacy scripts: `fetch_de.py`, `fetch_us.py`, `fetch_uk.py`, `fetch_au.py`, `fetch_nz.py`, `fetch_za.py`, `load_us_to_supabase.py`. Consider removing. | ⬜ |
| 4.3 | Consolidate duplicate workflows | `auto-scrape-forecasts.yml` and `auto-scrape-cb-forecasts.yml` appear to be duplicates. Consolidate. | ⬜ |
| 4.4 | Fix IMF metadata path inconsistency | `imf_forecasts.json` has metadata nested under a `metadata` key, but some code reads from top level. | ⬜ |

---

## Open Issues

### 🔴 Active Issues

#### 1. Live site out of sync with local codebase
- **Status:** GitHub repo has 2 commits, local has 13 countries + full automation
- **Impact:** Critical — users see stale 8-country dashboard
- **Fix:** Push local codebase to GitHub (Phase 0)

#### 2. Email notifications not arriving
- **Status:** Resend shows "Delivered" but emails not received in inbox
- **To investigate:**
  - Check Resend "To" field for correct recipient
  - Check spam/junk folder
  - Verify `NOTIFICATION_EMAIL` GitHub secret
  - Consider switching from `@resend.dev` to verified domain
- **Workaround:** Check Resend dashboard directly for notification content

#### 3. FRED API errors for Japan & Singapore
- **Error:** `400 Bad Request` for series JPNCPALTT01GYM659N and SGPCPIALLMINMEI
- **Cause:** These series don't support `units=pc1` parameter
- **Impact:** Low — dashboard still works, just can't auto-update these countries
- **Fix needed:** Update `monitor_updates.py` to handle these series differently

#### 4. Venezuela data stale (10 months)
- **Status:** Expected — BCV/FRED doesn't update VE frequently
- **Impact:** Low — VE page works, just shows old data
- **Fix:** Manual update from BCV/IMF sources when available

#### 5. Five countries not in automated CPI fetch
- **Countries:** JP, IN, KR, SG, VE
- **Impact:** Medium — these countries' CPI data won't auto-update
- **Fix:** Add FRED series or alternative fetch logic to `fetch_historical_cpi.py`

### ✅ Recently Fixed

- **Venezuela page "Error loading data"** (Jan 27): Fixed null target handling in country.js
- **Quarterly date format crash** (Jan 27): Fixed AU/NZ `2025-Q4` format in monitor script

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
| `cb_forecasts.json` | Central bank forecasts + policy rates | Manual (after MPC meetings) |
| `history/cb_forecast_history.json` | CB forecast snapshots | Manual (optional) |
| `history/imf_forecast_history.json` | IMF forecast snapshots | Manual (optional) |

### Frontend Files (in `docs/`)

| File | Purpose |
|------|---------|
| `index.html` | Overview page — inflation table, CB outlook, policy rates |
| `country.js` | Shared JS module for all country detail pages |
| `styles.css` | Shared styles (1,279 lines) |
| `{code}.html` | Country detail pages (13 total: us, ea, uk, ca, au, nz, za, jp, kr, sg, in, cn, ve) |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Automation (GitHub Actions)                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────┐  │
│  │monitor_updates. │ │send_notification│ │auto_scrape_cb_   │  │
│  │py               │ │.py (Resend)     │ │forecasts.py      │  │
│  └────────┬────────┘ └────────┬────────┘ └────────┬─────────┘  │
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
│  │index.html       │ │us.html, uk.html, ... ve.html         │  │
│  │(overview)       │ │(13 country pages)                    │  │
│  └─────────────────┘ └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
inflation-dashboard/
├── README.md                    # Project overview (needs update!)
├── METHODOLOGY.md               # Technical documentation
├── PROJECT_PLAN.md              # This file (internal reference)
├── MAINTENANCE.md               # Manual update guide
├── CHANGELOG.md                 # Version history (needs update)
├── LICENSE
├── .env.local                   # Local API keys (not committed)
├── .gitignore
│
├── scripts/
│   ├── fetch_historical_cpi.py  # ✅ FRED CPI fetch (8 countries — missing JP/IN/KR/SG/VE)
│   ├── fetch_imf_forecasts.py   # ✅ IMF WEO fetch
│   ├── auto_scrape_cb_forecasts.py  # ✅ CB forecast scraper (6 banks — missing Fed/BoJ/BOK/MAS/RBI/PBoC)
│   ├── fetch_cb_forecasts.py    # Older CB forecast fetcher (may be redundant)
│   ├── monitor_updates.py       # ✅ Checks FRED for new data
│   ├── send_notification.py     # ✅ Sends email via Resend
│   ├── send_weekly_alert.py     # Weekly alert logic (not wired to workflow)
│   ├── patch_cpi_supplements.py # Patches FRED gaps with manual data
│   ├── test_data_sources.py     # Data source testing
│   ├── fetch_ecb_forecast.py    # ECB-specific fetcher
│   ├── fetch_us_fed_forecast.py # Fed-specific fetcher
│   ├── fetch_uk_cpi.py          # UK CPI-specific fetcher
│   ├── fetch_au.py              # Legacy individual fetchers ─┐
│   ├── fetch_de.py              #                             │ Consider
│   ├── fetch_nz.py              #                             │ removing
│   ├── fetch_uk.py              #                             │ (pre-consolidation)
│   ├── fetch_us.py              #                             │
│   ├── fetch_za.py              #                            ─┘
│   └── load_us_to_supabase.py   # Legacy Supabase loader (abandoned)
│
├── data/                        # Working data directory
│   ├── historical_cpi.json      # Master CPI data
│   ├── imf_forecasts.json       # IMF forecasts
│   ├── cpi_supplements.json     # Manual CPI supplements (5 countries)
│   ├── weekly_snapshots.json    # Weekly alert snapshots
│   ├── inflation_data.js        # Legacy JS data file
│   ├── us_cpi.json              # Legacy per-country files ──┐
│   ├── uk_cpi.json              #                            │ Consider
│   ├── ca_cpi.json              #                            │ removing
│   ├── au_cpi.json              #                            │ (pre-consolidation)
│   ├── nz_cpi.json              #                            │
│   ├── za_cpi.json              #                            │
│   ├── cn_cpi.json              #                            │
│   ├── jp_cpi.json              #                            │
│   ├── ea_cpi.json              #                            │
│   ├── ch_cpi.json              #                            │
│   └── de_cpi.json              #                           ─┘
│
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview page
│   ├── us.html                  # Country pages (13 total)
│   ├── ea.html
│   ├── uk.html
│   ├── ca.html
│   ├── au.html
│   ├── nz.html
│   ├── za.html
│   ├── jp.html
│   ├── kr.html
│   ├── sg.html
│   ├── in.html
│   ├── cn.html
│   ├── ve.html
│   ├── styles.css               # Shared styles
│   ├── country.js               # Shared JS for country pages
│   ├── data_sources.md
│   ├── project_plan.md          # Older copy of project plan (in docs/)
│   └── data/
│       ├── historical_cpi.json  # Deployed CPI data
│       ├── imf_forecasts.json   # Deployed IMF forecasts
│       ├── cb_forecasts.json    # Deployed CB forecasts
│       └── history/
│           ├── cb_forecast_history.json
│           └── imf_forecast_history.json
│
└── .github/
    └── workflows/
        ├── monitor-updates.yml          # ✅ Mon & Thu 9am UTC — FRED check + email
        ├── update-data.yml              # ✅ Mon 12pm UTC — FRED fetch + commit
        ├── auto-scrape-forecasts.yml    # ✅ Mon & Thu 10am UTC — CB forecast scraper
        ├── auto-scrape-cb-forecasts.yml # Duplicate? Needs consolidation
        └── weekly-alert.yml             # Stub — not wired to send_weekly_alert.py
```

---

## Automation

### GitHub Actions Workflows

| Workflow | Schedule | Purpose | Status |
|----------|----------|---------|--------|
| `monitor-updates.yml` | Mon & Thu 9am UTC | Check FRED for new CPI data + email alerts | ✅ Working (commits directly) |
| `update-data.yml` | Mon 12pm UTC | Fetch CPI + IMF data from FRED, commit if changed | ✅ Working (commits directly) |
| `auto-scrape-forecasts.yml` | Mon & Thu 10am UTC | Scrape CB forecast pages | ✅ Defined (6 banks only) |
| `auto-scrape-cb-forecasts.yml` | ? | Appears to be duplicate of above | ⚠️ Needs consolidation |
| `weekly-alert.yml` | Mon 1pm UTC | Weekly data check | ⚠️ Stub — doesn't call send_weekly_alert.py |

### GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `FRED_API_KEY` | FRED API access |
| `RESEND_API_KEY` | Email notifications |
| `NOTIFICATION_EMAIL` | Recipient email |

### Automation Coverage Matrix

| Task | Automated | Manual | Gap |
|------|-----------|--------|-----|
| CPI data — US, EA, UK, CA, AU, NZ, ZA, CN | ✅ FRED fetch | Supplement if lags | — |
| CPI data — JP, IN, KR, SG, VE | ❌ Not in fetch script | Must update manually | 🔴 |
| CB forecasts — ECB, BoE, RBA, BoC, RBNZ, SARB | ✅ Auto-scraper (draft) | Review & approve | — |
| CB forecasts — Fed, BoJ, BOK, MAS, RBI, PBoC | ❌ No scraper | Must update manually | 🟡 |
| CB meeting reminders | ✅ monitor_updates.py | — | — |
| IMF WEO reminders (Apr/Oct) | ✅ monitor_updates.py | Update data | — |
| Stale data alerts | ✅ monitor_updates.py | — | — |
| Email notifications | ✅ Resend (delivery issues) | Check dashboard | 🟡 |
| Weekly material change alerts | ❌ Stub workflow | — | 🔴 |
| IMF forecast updates | ❌ | Manual 2x/year | — |

---

## Manual Maintenance Tasks

### Central Bank Forecast Updates

**When:** After major MPC meetings (varies by country)  
**What:** Edit `docs/data/cb_forecasts.json`  
**Key meetings with projections:**

| Country | Bank | Projection Schedule |
|---------|------|---------------------|
| 🇺🇸 US | FOMC | Mar, Jun, Sep, Dec (SEP) |
| 🇪🇺 EA | ECB | Mar, Jun, Sep, Dec (staff projections) |
| 🇬🇧 UK | BoE | Feb, May, Aug, Nov (MPR) |
| 🇨🇦 CA | BoC | Jan, Apr, Jul, Oct (MPR) |
| 🇦🇺 AU | RBA | Feb, May, Aug, Nov (SoMP) |
| 🇳🇿 NZ | RBNZ | Feb, May, Aug, Nov (MPS) |
| 🇿🇦 ZA | SARB | Jan, Mar, May, Jul, Sep, Nov |
| 🇯🇵 JP | BoJ | Jan, Apr, Jul, Oct (Outlook) |
| 🇰🇷 KR | BOK | Feb, May, Aug, Nov |
| 🇸🇬 SG | MAS | Apr, Oct (policy statement) |
| 🇮🇳 IN | RBI | Feb, Apr, Jun, Aug, Oct, Dec |

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

### Countries NOT in Automated CPI Fetch

| Country | Reason | Workaround |
|---------|--------|------------|
| JP | Not added to `fetch_historical_cpi.py` | Manual update |
| IN | Not added to `fetch_historical_cpi.py` | Manual update |
| KR | Not added to `fetch_historical_cpi.py` | Manual update |
| SG | Not added to `fetch_historical_cpi.py` | Manual update |
| VE | Not added to `fetch_historical_cpi.py` | Manual update from IMF/BCV |

### Special Cases

- **Venezuela:** No inflation target; `target: null` in data files. BCV publishes irregularly.
- **Singapore:** MAS uses exchange rate policy (S$NEER band), not interest rates.
- **Australia:** Transitioned from quarterly to monthly CPI in Oct 2025.
- **South Africa:** Target changed from 3-6% to 2-4% (3% midpoint) in Nov 2025 — first change in 25 years.

---

## Session Recovery Guide

If starting a new session or recovering from a crash:

### 1. Check Current State
```bash
cd ~/Projects/inflation-dashboard

# What's the latest commit?
git log --oneline -5

# Any uncommitted changes?
git status

# What files exist?
ls -la docs/data/
```

### 2. Check Data Freshness
```bash
# Check last update date
head -5 docs/data/historical_cpi.json

# Check CB forecast dates
python3 -c "
import json
with open('docs/data/cb_forecasts.json') as f:
    cb = json.load(f)
for code in cb.get('display_order', []):
    fc = cb['forecasts'].get(code, {})
    print(f\"{code}: {fc.get('publication_date', 'N/A')}\")
"
```

### 3. Test the Site
- Open https://jing-ny.github.io/inflation-dashboard/
- Verify all 13 countries appear in the table
- Click Venezuela page (tests null target handling)
- Check that "As Of" dates are within the last quarter

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
- **Substack:** https://inflationofficially.substack.com

---

*This document should be updated whenever significant architectural changes are made.*
