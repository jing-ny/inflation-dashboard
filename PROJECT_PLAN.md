# Inflation Dashboard - Project Plan & Architecture

**Last Updated:** March 24, 2026
**Purpose:** Reference document to maintain consistency across sessions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [To-Do List](#to-do-list)
4. [Known Bugs](#known-bugs)
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
**Newsletter:** https://inflationofficially.substack.com

**Purpose:** A source-first dashboard tracking official CPI inflation data and central bank forecasts across 15 economies.

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
| VE | Venezuela | BCV | BCV | Irregular |

---

## Current State (as of March 24, 2026)

### What Works
- Dashboard fully deployed on GitHub Pages, all 13 country pages render correctly
- `fetch_historical_cpi.py` covers all 15 countries via FRED + ECB APIs
- 5 GitHub Actions workflows running on schedule
- `update_cpi.py` and `batch_update_cpi.py` manual update tools functional
- Substack newsletter signup embedded on homepage
- CB forecasts and IMF forecasts populated for all 15 countries
- 10-year CPI history with Chart.js visualization on country pages
- CPI data current through Feb 2026 for most countries (updated Mar 24)
- CB forecasts updated to latest meetings (Mar 24)

### Data Freshness

**Live site data as of March 24, 2026:**

| Data | Last Updated | Should Be | Gap |
|------|-------------|-----------|-----|
| CPI (10 countries) | Feb 2026 | Feb 2026 | OK |
| CPI (UK, AU) | Jan 2026 | Jan 2026 | OK (Feb releasing Mar 25) |
| CPI (NZ) | Q4 2025 | Q4 2025 | OK (quarterly) |
| CB Forecasts | Mar 2026 | Mar 2026 | OK |
| IMF WEO | Oct 2025 | Oct 2025 | OK (next: Apr 2026) |

**Ongoing concern:** FRED API lags official releases by 1-6 months for most international series. The automated `update-data.yml` workflow runs every Monday and succeeds, but FRED has no new data to pull, so nothing gets committed. Manual updates via `update_cpi.py` remain necessary for timely data.

### Workflow Status

| Workflow | Last Run | Status |
|----------|----------|--------|
| Update Inflation Data | 2026-03-23 | Success (no new data from FRED) |
| Monitor & Update Data | 2026-03-23 | Failure (commit step — no changes to commit) |
| Auto-Scrape CB Forecasts | 2026-03-23 | Success (no changes detected) |
| Weekly Alert | 2026-03-23 | Success |

---

## To-Do List

### Phase 1: Restore Data Freshness (Priority: Critical)

| # | Task | Details | Status |
|---|------|---------|--------|
| 1.1 | Manual CPI update for all 15 countries | Updated Jan + Feb 2026 values for all 15 countries. Added 5 missing countries (JP, IN, KR, SG, VE) to `historical_cpi.json`. UK/AU have Jan only (Feb releases Mar 25). NZ updated to Q4 2025. | **Done** (Mar 24) |
| 1.2 | Update CB forecasts | Updated 10 central banks to latest meetings: Fed Mar SEP, ECB Mar, BoE Feb MPR, BoC Jan MPR, RBA Feb SoMP, RBNZ Feb MPS, SARB Jan, BoJ Mar, RBI Feb, BOK Feb. Policy rates and projections current. SG/VE/CN unchanged (no new publications). | **Done** (Mar 24) |
| 1.3 | Add direct API sources for key countries | Reduce FRED dependency. Priority: BLS API for US, Stats Canada API for CA, ONS API for UK. Each country 2-3 hours. | To Do |
| 1.4 | Fix Monitor workflow commit failure | Added `permissions: contents: write` (root cause was 403 on push). Also aligned git config and added summary step to match `update-data.yml` pattern. | **Done** (Mar 24) |

### Phase 2: Fix Known Bugs (Priority: High)

| # | Task | Details | Status |
|---|------|---------|--------|
| 2.1 | Clean up `styles.css` duplication | Deduplicated from 1279 → 604 lines. Removed 4 redundant copies of policy change CSS block. | **Done** (Mar 24) |
| 2.2 | Remove `test` text from `index.html` | Removed bare `test` string. | **Done** (Mar 24) |
| 2.3 | Fix `send_weekly_alert.py` data path | Fixed path to `docs/data/historical_cpi.json` and changed key access to read country codes directly from top level. | **Done** (Mar 24) |
| 2.4 | Add argparse to `auto_scrape_cb_forecasts.py` | Added argparse for `--force`, `--country`, `--dry-run`. Wired into scraper logic. | **Done** (Mar 24) |
| 2.5 | Unify FRED series between scripts | Updated `monitor_updates.py` to use same series as `fetch_historical_cpi.py` (US: CPIAUCNS, JP: JPNCPIALLMINMEI). | **Done** (Mar 24) |
| 2.6 | Implement `update_forecast_history()` | Implemented in `monitor_updates.py`. Reads CB forecasts, appends timestamped snapshot to `docs/data/history/cb_forecast_history.json`. | **Done** (Mar 24) |
| 2.7 | Rotate leaked API keys | Commit `c681654` removed hardcoded API keys, but they remain in git history. Rotate FRED, Supabase, and Resend keys. | **Manual** — requires key regeneration on provider dashboards + GitHub Secrets update |

### Phase 3: Newsletter Automation (Priority: Medium)

| # | Task | Details | Status |
|---|------|---------|--------|
| 3.1 | Build change detection script | Already working in `send_weekly_alert.py` (fixed in Phase 2). Detects material changes (≥0.3pp or direction reversal) via snapshot comparison. | **Done** (Mar 24) |
| 3.2 | Claude API draft generation | New `scripts/generate_newsletter.py`. Uses Anthropic SDK (`claude-sonnet-4-20250514`) to generate 300-500 word drafts from CPI changes + CB/IMF forecast context. Supports `--dry-run` and `--output`. | **Done** (Mar 24) |
| 3.3 | GitHub Actions integration | New `newsletter-draft.yml`. Triggers on `historical_cpi.json` changes or manual dispatch. Generates draft, commits to `docs/drafts/`, optional email notification. Requires `ANTHROPIC_API_KEY` secret. | **Done** (Mar 24) |
| 3.4 | Wire weekly alert workflow | Rewired `weekly-alert.yml` to call `send_weekly_alert.py`. Added snapshot commit step, proper env vars, permissions. | **Done** (Mar 24) |

### Phase 4: Expansion & Polish (Priority: Low)

| # | Task | Details | Status |
|---|------|---------|--------|
| 4.1 | Add Core CPI + US PCE tracking | Added Core CPI (3.1%), PCE (2.5%), Core PCE (2.6%) as supplementary metrics on US page. Data in `historical_cpi.json` under `supplementary` field. | **Done** (Mar 24) |
| 4.2 | Add Brazil and Mexico | Added BR (IBGE/BCB, 14.25%) and MX (INEGI/Banxico, 9.50%). Country pages, CPI data, CB/IMF forecasts, FRED series. Now 15 countries. | **Done** (Mar 24) |
| 4.3 | Make year columns dynamic in index.html | Outlook table headers now auto-advance based on `new Date().getFullYear()`. | **Done** (Mar 24) |
| 4.4 | Add table sorting on index page | Click column headers to sort/toggle. Visual ▲/▼ indicator. Numeric-aware sorting. | **Done** (Mar 24) |
| 4.5 | Clean up legacy files | Removed 11 legacy scripts, `inflation_data.js`, 4 semi-redundant fetch scripts. | **Done** (Mar 24) |
| 4.6 | Consolidate duplicate workflows | Removed `auto-scrape-forecasts.yml` (kept `auto-scrape-cb-forecasts.yml`). | **Done** (Mar 24) |

---

## Known Bugs

### Active

| # | Bug | Impact | File |
|---|-----|--------|------|
| B7 | Monitor workflow fails on commit step | Attempts git commit when there are no changes | `.github/workflows/monitor-updates.yml` |
| B8 | SSL verification disabled in CB scraper | `ssl_context.verify_mode = ssl.CERT_NONE` — security risk | `scripts/auto_scrape_cb_forecasts.py` |
| B9 | CB scraper has hardcoded 2024 fallback URLs | ECB, BoE, RBA, BoC, RBNZ fallback URLs point to 2024 pages | `scripts/auto_scrape_cb_forecasts.py` |
| B10 | JP and KR FRED series discontinued | JPNCPIALLMINMEI (COICOP 1999) and KORCPIALLMINMEI (discontinued Nov 2023) — auto-update effectively broken for these countries | `scripts/fetch_historical_cpi.py` |

### Resolved (since Feb 2026)

| Bug | Resolution | Date |
|-----|-----------|------|
| B1 | CSS deduplicated (1279 → 604 lines) | Mar 2026 |
| B2 | Removed bare `test` text from index.html | Mar 2026 |
| B3 | Fixed send_weekly_alert.py path + key structure | Mar 2026 |
| B4 | Added argparse to auto_scrape_cb_forecasts.py | Mar 2026 |
| B5 | Unified FRED series in monitor_updates.py | Mar 2026 |
| B6 | Implemented update_forecast_history() | Mar 2026 |
| Live site out of sync (2 commits, 8 countries) | Full codebase pushed to GitHub | Feb 2026 |
| Venezuela page "Error loading data" | Null target handling fixed in country.js | Jan 2026 |
| Quarterly date format crash in monitor | Fixed AU/NZ `2025-Q4` format | Jan 2026 |
| Dec 2025 CPI values incorrect for 8 countries | Corrected from official sources | Feb 2026 |
| Data architecture: dual `data/` and `docs/data/` | Consolidated to `docs/data/` as single source | Feb 2026 |

---

## Architecture

### Core Principle: Single Source of Truth

```
Python Scripts (fetch / update data)
        ↓
    docs/data/ JSON Files (single source of truth)
        ↓
    HTML/JS Pages (read and display via fetch())
```

### Data Files (in `docs/data/`)

| File | Contents | Updated By |
|------|----------|------------|
| `historical_cpi.json` | 10-year CPI history + latest/previous readings for 15 countries | `fetch_historical_cpi.py` (auto) + `update_cpi.py` (manual) |
| `cb_forecasts.json` | Central bank forecasts, policy rates, key quotes | Manual edit after MPC meetings |
| `imf_forecasts.json` | IMF WEO inflation projections | Manual (2x/year: Apr + Oct) |
| `cpi_supplements.json` | Manual CPI supplements when FRED lags | Manual |
| `weekly_snapshots.json` | Weekly alert snapshots for change detection | `send_weekly_alert.py` (not functional) |
| `history/cb_forecast_history.json` | CB forecast revision tracking | Placeholder (not implemented) |
| `history/imf_forecast_history.json` | IMF forecast revision tracking | Placeholder (not implemented) |

### Frontend Files (in `docs/`)

| File | Purpose |
|------|---------|
| `index.html` | Overview — inflation table, CB outlook, policy rates |
| `country.js` | Shared JS module for all 13 country detail pages |
| `styles.css` | Shared styles (has duplication issue — see B1) |
| `{code}.html` | Country detail pages (us, ea, uk, ca, au, nz, za, jp, kr, sg, in, cn, ve) |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  Data Sources                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ FRED API │  │ ECB API  │  │ Official │  │ Manual Input │   │
│  │ (13 ctry)│  │ (EA only)│  │ Websites │  │ update_cpi.py│   │
│  └────┬─────┘  └────┬─────┘  └─────┬────┘  └──────┬───────┘   │
└───────┼──────────────┼──────────────┼──────────────┼───────────┘
        │              │              │              │
        ↓              ↓              ↓              ↓
┌────────────────────────────────────────────────────────────────┐
│                    docs/data/ (single source of truth)          │
│  ┌───────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │historical_cpi.json│ │cb_forecasts.json│ │imf_forecasts.  │  │
│  │                   │ │                │ │json            │  │
│  └─────────┬─────────┘ └───────┬────────┘ └───────┬────────┘  │
└────────────┼───────────────────┼───────────────────┼───────────┘
             ↓                   ↓                   ↓
┌────────────┴───────────────────┴───────────────────┴───────────┐
│                    GitHub Pages (docs/)                          │
│  ┌─────────────────┐  ┌───────────────────────────────────┐   │
│  │index.html       │  │us.html, ea.html, ... ve.html      │   │
│  │(overview)       │  │(13 country detail pages)           │   │
│  └─────────────────┘  └───────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
inflation-dashboard/
├── README.md
├── PROJECT_PLAN.md              # This file
├── METHODOLOGY.md               # Data methodology documentation
├── CPI_UPDATE_GUIDE.md          # Official source URLs + release calendar
├── MAINTENANCE.md               # Manual update procedures
├── CHANGELOG.md
├── LICENSE
├── .env.local                   # Local API keys (gitignored)
├── .gitignore
├── update_cpi.py                # Manual CPI update tool (single country)
├── batch_update_cpi.py          # Manual CPI update tool (batch)
│
├── scripts/
│   ├── fetch_historical_cpi.py  # FRED/ECB CPI fetch (all 15 countries)
│   ├── fetch_imf_forecasts.py   # IMF WEO fetch
│   ├── auto_scrape_cb_forecasts.py  # CB forecast scraper (6 banks: ECB, BoE, RBA, BoC, RBNZ, SARB)
│   ├── monitor_updates.py       # FRED freshness check + CB meeting calendar
│   ├── send_notification.py     # Email via Resend API
│   ├── send_weekly_alert.py     # Weekly alert logic (BUG: wrong data path, non-functional)
│   ├── patch_cpi_supplements.py # Patches FRED gaps
│   ├── test_data_sources.py     # Data source testing
│   └── test_data_sources.py     # Data source testing
│
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview page
│   ├── {country}.html           # 13 country detail pages
│   ├── styles.css               # Shared styles (BUG: CSS duplicated 5x)
│   ├── country.js               # Shared JS for country pages
│   ├── data_sources.md          # Legacy doc (in docs/)
│   ├── project_plan.md          # Legacy plan copy (in docs/)
│   └── data/                    # ★ SINGLE SOURCE OF TRUTH ★
│       ├── historical_cpi.json  # CPI data for all 15 countries
│       ├── cb_forecasts.json    # Central bank forecasts + policy rates
│       ├── imf_forecasts.json   # IMF WEO projections
│       ├── cpi_supplements.json # Manual CPI supplements
│       ├── weekly_snapshots.json
│       └── history/
│           ├── cb_forecast_history.json   # Placeholder
│           └── imf_forecast_history.json  # Placeholder
│
└── .github/workflows/
    ├── update-data.yml              # Mon 12pm UTC — FRED/ECB fetch + commit
    ├── monitor-updates.yml          # Mon & Thu 9am UTC — freshness check + email
    ├── auto-scrape-cb-forecasts.yml # Mon & Thu 10am UTC — CB forecast scraper
    └── weekly-alert.yml             # Mon 1pm UTC — stub (just prints data)
```

---

## Automation

### GitHub Actions Workflows

| Workflow | File | Schedule | Purpose | Status |
|----------|------|----------|---------|--------|
| Update Inflation Data | `update-data.yml` | Mon 12pm UTC | Fetch CPI + IMF from FRED/ECB, commit if changed | Running, but FRED lag means no new data |
| Monitor & Update Data | `monitor-updates.yml` | Mon & Thu 9am UTC | Check FRED for updates, email alerts | Running, commit step fails (B7) |
| Auto-Scrape CB Forecasts | `auto-scrape-cb-forecasts.yml` | Mon & Thu 10am UTC | Scrape CB forecast pages | Running, CLI args now functional |
| Weekly Alert | `weekly-alert.yml` | Mon 1pm UTC | Data check | Stub — does not call `send_weekly_alert.py` |

### GitHub Secrets Required

| Secret | Purpose | Status |
|--------|---------|--------|
| `FRED_API_KEY` | FRED API access | Configured |
| `RESEND_API_KEY` | Email notifications | Configured |
| `NOTIFICATION_EMAIL` | Recipient email | Configured |

### Automation Coverage

| Task | Automated? | Notes |
|------|-----------|-------|
| CPI data fetch (all 13) | Yes (FRED/ECB) | But FRED lags 1-6 months for most countries |
| CPI manual update tool | Yes (CLI) | `update_cpi.py` — requires human to look up values |
| CB forecasts (6 banks) | Partial | ECB, BoE, RBA, BoC, RBNZ, SARB — scraper generates drafts |
| CB forecasts (7 banks) | No | Fed, BoJ, BOK, MAS, RBI, PBoC, IMF(VE/CN) — manual only |
| CB meeting reminders | Yes | `monitor_updates.py` |
| IMF WEO reminders | Yes | `monitor_updates.py` (Apr/Oct) |
| Stale data alerts | Yes | `monitor_updates.py` (75-day threshold) |
| Email notifications | Yes | Resend API |
| Weekly material change alert | No | `send_weekly_alert.py` exists but is broken (B3) |
| Newsletter draft generation | No | Planned (Phase 3) |

---

## Manual Maintenance Tasks

### Monthly: CPI Data Update

**When:** After each country's CPI release (see schedule in CPI_UPDATE_GUIDE.md)
**How:**
```bash
# Example: update US January 2026 data
python3 update_cpi.py -c US -d 2026-01 -v 2.8

# View current state
python3 update_cpi.py --show-all

# Commit
git add docs/data/historical_cpi.json
git commit -m "Update CPI data: US Jan 2026"
git push
```

### After CB Meetings: Forecast Update

**When:** After major MPC meetings with new projections
**Key projection schedules:**

| Country | Bank | Months with Full Projections |
|---------|------|------------------------------|
| US | FOMC | Mar, Jun, Sep, Dec (SEP) |
| EA | ECB | Mar, Jun, Sep, Dec (staff projections) |
| UK | BoE | Feb, May, Aug, Nov (MPR) |
| CA | BoC | Jan, Apr, Jul, Oct (MPR) |
| AU | RBA | Feb, May, Aug, Nov (SoMP) |
| NZ | RBNZ | Feb, May, Aug, Nov (MPS) |
| ZA | SARB | Jan, Mar, May, Jul, Sep, Nov |
| JP | BoJ | Jan, Apr, Jul, Oct (Outlook) |
| KR | BOK | Feb, May, Aug, Nov |
| SG | MAS | Apr, Oct (policy statement) |
| IN | RBI | Feb, Apr, Jun, Aug, Oct, Dec |

**How:** Edit `docs/data/cb_forecasts.json` — update `publication_date`, `projections`, `policy_rate`, `key_quote`.

### Twice Yearly: IMF WEO Update

**When:** April and October
**Source:** https://www.imf.org/external/datamapper/PCPIPCH@WEO
**How:** Edit `docs/data/imf_forecasts.json`

---

## Data Sources & Known Limitations

### FRED API Lag (Core Problem)

FRED OECD series lag official releases significantly:

| Country | FRED Series | Typical Lag | Mitigation |
|---------|-------------|-------------|------------|
| US | CPIAUCNS | 2-4 weeks | BLS publishes ~13th; manual update or add BLS API |
| UK | GBRCPIALLMINMEI | 1-2 months | Manual from ONS |
| CA | CANCPIALLMINMEI | 1-2 months | Manual from StatCan |
| AU | AUSCPIALLQINMEI | 1-2 quarters | Quarterly OECD series; ABS now publishes monthly |
| NZ | NZLCPIALLQINMEI | 1-2 quarters | Quarterly only |
| ZA | ZAFCPIALLMINMEI | 3-6 months | Manual from Stats SA |
| VE | FPCPITOTLZGVEN | 6-12 months | IMF/BCV manual update |

### Discontinued / Broken FRED Series

| Country | Series | Issue | Fallback |
|---------|--------|-------|----------|
| JP | JPNCPIALLMINMEI | COICOP 1999 — may stop updating | World Bank annual (FPCPITOTLZGJPN) + manual |
| KR | KORCPIALLMINMEI | Discontinued Nov 2023 | World Bank annual (FPCPITOTLZGKOR) + manual |
| SG | FPCPITOTLZGSGP | World Bank annual only | Manual from SingStat |

### Special Cases

- **Venezuela:** No inflation target (`target: null`). BCV publishes irregularly. Data relies on IMF.
- **Singapore:** MAS uses exchange rate policy (S$NEER band), not interest rates.
- **Australia:** Transitioned from quarterly to monthly CPI in late 2025. FRED still quarterly.
- **South Africa:** Target changed from 3-6% to 2-4% (3% midpoint) in Nov 2025.
- **Euro Area:** Uses ECB SDMX API directly (not FRED) — more timely than FRED.

---

## Session Recovery Guide

### 1. Check Current State
```bash
cd ~/Projects/inflation-dashboard

git log --oneline -5
git status

# Data freshness
python3 update_cpi.py --show-all

# CB forecast dates
python3 -c "
import json
with open('docs/data/cb_forecasts.json') as f:
    cb = json.load(f)
for code in cb.get('display_order', []):
    fc = cb['forecasts'].get(code, {})
    print(f\"{code}: {fc.get('publication_date', 'N/A')}\")
"
```

### 2. Check Automation
```bash
# GitHub Actions status
gh run list --limit 10

# Check if data was updated recently
git log --oneline --since="30 days ago" -- docs/data/historical_cpi.json
```

### 3. Test the Site
- Open https://jing-ny.github.io/inflation-dashboard/
- Verify all 15 countries appear in the table
- Check "As Of" dates — should be within the last 1-2 months
- Click Venezuela page (tests null target handling)

### 4. If Data Is Stale
```bash
# Option A: Run automated fetch (may not help if FRED lags)
python3 scripts/fetch_historical_cpi.py

# Option B: Manual update from official sources
# See CPI_UPDATE_GUIDE.md for URLs
python3 update_cpi.py -c US -d YYYY-MM -v X.X
```

---

## Useful Links

- **Dashboard:** https://jing-ny.github.io/inflation-dashboard/
- **GitHub repo:** https://github.com/jing-ny/inflation-dashboard
- **Actions:** https://github.com/jing-ny/inflation-dashboard/actions
- **Resend:** https://resend.com/emails
- **FRED:** https://fred.stlouisfed.org/
- **IMF DataMapper:** https://www.imf.org/external/datamapper/PCPIPCH@WEO
- **Substack:** https://inflationofficially.substack.com
- **Evaluation Report:** [docs/EVALUATION-REPORT.md](docs/EVALUATION-REPORT.md)

---

*This document should be updated whenever significant architectural changes are made.*
