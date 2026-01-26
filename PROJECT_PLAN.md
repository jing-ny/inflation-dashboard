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
│   fetch_imf_forecasts.py   ──►  imf_forecasts.json   ──►        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

GitHub Actions (weekly):
  - Runs all fetch scripts
  - Copies JSON to docs/data/
  - Commits if changed
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
│   ├── fetch_historical_cpi.py  # ✅ Fetches CPI from FRED/BLS/etc
│   ├── fetch_cb_forecasts.py    # ✅ Fetches/stores CB forecasts
│   └── fetch_imf_forecasts.py   # ✅ Fetches IMF WEO projections
│
├── data/                        # Raw data (not in docs/)
│   ├── historical_cpi.json
│   ├── cb_forecasts.json
│   └── imf_forecasts.json
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
        ├── update-data.yml      # Weekly data fetch (Mon 9am UTC)
        └── weekly-alert.yml     # Weekly status check (Mon 1pm UTC)
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

### 🔲 P2 — Enhancements (Future)

| Task | Description | Status |
|------|-------------|--------|
| Add more countries | Japan, Singapore, India, etc. | 🔲 Not started |
| Email subscription | Alerts for material changes | 🔲 Not started |
| Supabase backend | Store forecast history | 🔲 Not started |
| Auto-scrape CB forecasts | RBA, BoE, ECB page scraping | 🔲 Not started |
| Mobile optimization | Improve responsive design | 🔲 Not started |

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

### Central Bank Forecasts (fetch_cb_forecasts.py)

| Country | Source | Method | Status |
|---------|--------|--------|--------|
| 🇺🇸 US | FOMC SEP | FRED API + Manual | ✅ Dec 2025 |
| 🇪🇺 EA | ECB Staff Projections | ECB API + Manual | ✅ Dec 2025 |
| 🇬🇧 UK | BoE MPR | Manual | ✅ Nov 2025 |
| 🇦🇺 AU | RBA SMP | Manual | ✅ Nov 2025 |
| 🇨🇦 CA | BoC MPR | Manual | ✅ Oct 2025 |
| 🇳🇿 NZ | RBNZ MPS | Manual | ✅ Nov 2025 |
| 🇿🇦 ZA | SARB MPC | Manual | ✅ Nov 2025 |
| 🇨🇳 CN | IMF (no CB forecasts) | IMF API | ✅ Dec 2025 |

### IMF Forecasts (fetch_imf_forecasts.py)

| Source | Frequency | Status |
|--------|-----------|--------|
| IMF WEO | Twice yearly (Apr, Oct) | ✅ Working |

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
- **Status:** ✅ Updated

### weekly-alert.yml (Status Check)

- **Schedule:** Every Monday at 13:00 UTC
- **Runs:** Simple data validation check
- **Status:** ✅ Fixed (was failing, now simplified)

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

# Test fetch scripts locally
python scripts/fetch_historical_cpi.py --help 2>/dev/null || python scripts/fetch_historical_cpi.py
python scripts/fetch_cb_forecasts.py --no-api
```

---

## Key Commits

| Date | Commit | Description |
|------|--------|-------------|
| 2026-01-26 | (latest) | Update workflow to fetch all data sources |
| 2026-01-26 | - | Add fetch_cb_forecasts.py |
| 2026-01-26 | - | Fix weekly alert workflow |
| 2026-01-26 | 7a93704 | Single source of truth for forecasts |
| 2026-01-26 | 00d7bfa | Working state after revert |

---

## README Template (Preferred Style)

For reference, the README uses this clean, minimal style:

- Brief tagline
- "Why This Exists" section
- "What This Does / Does Not Do" lists
- Coverage table
- Data sources explanation
- Update frequency
- Disclaimer
- License link

No hype, just facts. Source-first philosophy.

---

## Next Steps (When Ready)

### To add a new country:

1. Add config to `fetch_historical_cpi.py` COUNTRIES dict
2. Add forecast data to `fetch_cb_forecasts.py` MANUAL_FORECASTS dict
3. Create `{code}.html` country page
4. Add to `index.html` display order
5. Run fetch scripts and deploy

### To enable email alerts:

1. Sign up for Resend (https://resend.com)
2. Add `RESEND_API_KEY` to GitHub Secrets
3. Add `ALERT_RECIPIENTS` to GitHub Secrets
4. Update `weekly-alert.yml` with email sending logic

### To add forecast scraping:

1. Identify scrapeable pages (RBA, ECB have good HTML)
2. Add scraper functions to `fetch_cb_forecasts.py`
3. Test thoroughly before enabling automation
