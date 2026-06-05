# Methodology

Technical documentation for the Inflation Monitor dashboard.

**Last Updated:** May 13, 2026

> **Operating principles** that govern how this project handles data quality, automation gaps, and staleness live in **[CLAUDE.md](CLAUDE.md)**. Read that first if you're proposing changes to scrapers or data shape — particularly:
> - No manual entry as a fallback when a scraper breaks (fix it or defer)
> - Every number is validated, or labeled as not yet validated
> - Every record carries provenance (`source_url` + a date field)
> - Stale data must be visibly stale (see Freshness Indicators below)
> - Trust the anomaly detector — don't silence the alarm

---

## Overview

This project fetches official inflation statistics and central bank forecasts from public APIs and official sources, stores them in JSON files, and displays them on a static dashboard hosted via GitHub Pages.

All data is stored in `docs/data/` as the single source of truth.

---

## Freshness Indicators

Every data point displayed on the dashboard is rendered with a colored "freshness pill" that ages green → amber → red against the source's expected publication cadence. This is enforced by [`docs/freshness.js`](docs/freshness.js) and is the visible side of CLAUDE.md principle #4.

| Data type | Green | Amber | Red |
|---|---|---|---|
| **Monthly CPI** (Current Inflation table, country-page hero) | ≤ 75 days | ≤ 120 days | > 120 days |
| **Quarterly CPI** (e.g. NZ — auto-detected from `YYYY-Qn`) | ≤ 135 days | ≤ 225 days | > 225 days |
| **CB forecasts** (Outlook table) | ≤ 120 days | ≤ 180 days | > 180 days |

Each table also has a **footer summary** counting current / stale / very-stale entries, and the threshold definitions are restated for transparency.

**Why the CPI thresholds are not tighter — and are cadence-aware.** The age is measured from the data point's **reference month/quarter** (day 1), *not* from its release date. But official CPI is released a few weeks *after* its reference period, so the freshest-possible monthly print is already ~45–75 days "old" by this measure, and a quarterly print (e.g. NZ) stays current for a full quarter. Earlier (tighter, monthly-only) thresholds therefore flagged up-to-date data as stale and rendered quarterly series red while current. The current thresholds track each series' real cadence — quarterly is auto-detected from the `YYYY-Qn` date shape — so the colors mean:

- **green** ≈ "this is the latest published release",
- **amber** ≈ "roughly one release behind",
- **red** ≈ "genuinely lagging" (the underlying source, or our pull from it, has fallen behind — see *Data sourcing and lag* below).

This keeps real staleness visible (CLAUDE.md #4) without false positives on current data.

**Disabled-scraper treatment (CLAUDE.md #4, layer 3).** Forecast rows whose auto-scraper is intentionally off render a distinct "paused" pill (not red) so a *missing scraper* isn't conflated with a *stale source*. IMF-sourced rows (CN — central banks that publish no forecast) render a neutral "IMF WEO" badge instead. As of this writing the BoE (#10), SARB (#12) and MAS-SPF (#42) scrapers have landed; RBNZ (#6) remains paused.

---

## Data Collection

### Actual Inflation (CPI)

| Country | Primary Source | Verification Source | Frequency |
|---------|----------------|---------------------|-----------|
| 🇺🇸 United States | FRED (CPIAUCNS) | [BLS](https://www.bls.gov/cpi/) | Monthly |
| 🇪🇺 Euro Area | FRED (CP0000EZ19M086NEST) | [Eurostat](https://ec.europa.eu/eurostat/web/hicp) | Monthly |
| 🇬🇧 United Kingdom | FRED (GBRCPIALLMINMEI) | [ONS](https://www.ons.gov.uk/economy/inflationandpriceindices) | Monthly |
| 🇨🇦 Canada | FRED (CANCPIALLMINMEI) | [StatCan](https://www.statcan.gc.ca/) | Monthly |
| 🇦🇺 Australia | FRED (AUSCPIALLQINMEI) | [ABS](https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/) | Monthly* |
| 🇳🇿 New Zealand | FRED (NZLCPIALLQINMEI) | [Stats NZ](https://www.stats.govt.nz/indicators/consumers-price-index-cpi/) | Quarterly |
| 🇿🇦 South Africa | FRED (ZAFCPIALLMINMEI) | [Stats SA](https://www.statssa.gov.za/) | Monthly |
| 🇯🇵 Japan | FRED (JPNCPALTT01IXNBM) | [MIC](https://www.stat.go.jp/english/data/cpi/) | Monthly |
| 🇨🇳 China | FRED (CHNCPIALLMINMEI) | [NBS](https://www.stats.gov.cn/english/) | Monthly |
| 🇮🇳 India | FRED (INDCPIALLMINMEI) | [MOSPI](https://www.mospi.gov.in/) | Monthly |
| 🇰🇷 South Korea | FRED (KORCPALTT01IXNBM) | [KOSTAT](https://kostat.go.kr/) | Monthly |
| 🇸🇬 Singapore | FRED (FPCPITOTLZGSGP) | [SingStat](https://www.singstat.gov.sg/) | Monthly |

*Australia transitioned to monthly CPI in late 2025. Historical data is quarterly.

**Notes:**
- All series measure **headline CPI (All Items)** year-over-year percentage change
- FRED OECD series use base year 2015=100
- US BLS series uses base year 1982-84=100
- Japan series changed from JPNCPIALLMINMEI (discontinued Jun 2021) to JPNCPALTT01IXNBM (COICOP 2018)
- South Korea series changed from KORCPIALLMINMEI (discontinued Nov 2023) to KORCPALTT01IXNBM (COICOP 2018)

---

## Data Verification Process

As of February 2026, all CPI values are verified against official government sources before publication.

### Typical Release Schedule

| Country | Typical Release Day | Notes |
|---------|---------------------|-------|
| 🇰🇷 South Korea | 1st of month | First major release |
| 🇨🇳 China | 9th of month | |
| 🇮🇳 India | 12th of month | |
| 🇺🇸 United States | 13th of month | BLS CPI report |
| 🇬🇧 United Kingdom | 15th of month | |
| 🇨🇦 Canada | 17th of month | |
| 🇪🇺 Euro Area | 17th of month | Flash estimate earlier |
| 🇿🇦 South Africa | 19th of month | |
| 🇯🇵 Japan | 19th of month | |
| 🇸🇬 Singapore | 23rd of month | |
| 🇦🇺 Australia | 28th of month | Quarterly: late Jan/Apr/Jul/Oct |
| 🇳🇿 New Zealand | Quarterly | Mid-month of Jan/Apr/Jul/Oct |

### Data sourcing, lag, and runner reachability

CPI actuals are fetched per country by [`scripts/fetch_historical_cpi.py`](scripts/fetch_historical_cpi.py). Each country's config carries an `api` field that selects the fetch path; the script **merges** (never blindly overwrites) and **only advances a value when the source has a genuinely newer reading**, so a laggy source can't roll a country *backwards*.

**Two classes of source:**

- **Direct primary/national API (fresh):** US → BLS, Euro Area → ECB, UK → ONS, Canada → StatCan, Australia → ABS (monthly CPI indicator, #50). These track the national release closely.
- **FRED's OECD relay (laggy):** the rest (NZ, ZA, JP, CN, IN, KR, BR, MX; SG via World Bank). The OECD aggregates and **re-publishes national CPI with a 1–3 month delay (sometimes 6–12)**, so these rows can sit a release or two behind the national agency *even though the weekly `Update Inflation Data` workflow runs and succeeds.* This — not a broken pipeline — is the usual reason a Current Inflation cell reads amber/red.

| Country | Source path | Typical lag vs national release |
|---------|-------------|---------------------------------|
| US, EA, UK, CA, AU | Direct (BLS / ECB / ONS / StatCan / ABS) | ~current |
| South Africa | FRED-OECD | 6–12 months |
| New Zealand | FRED-OECD (quarterly) | quarterly cadence |
| Japan, Korea | FRED (COICOP index) | 1–3 months; manual supplement sometimes needed |
| China, India | FRED-OECD | 1–3 months |
| Singapore | FRED (World Bank annual — OECD series broken) | coarse |

**Runner reachability is the gating constraint.** "Just switch the laggy countries to their national API" is the obvious fix (tracked per country in issues [#50–#60](https://github.com/jing-ny/inflation-dashboard/issues)), **but it only works if that API answers from where our automation actually runs** — GitHub Actions (Azure-hosted runners). Several national statistics APIs do **not** route to those cloud IPs. Two observed outcomes: the ABS Data API (`data.api.abs.gov.au`) **is** reachable from runners and now sources Australia directly (#50), whereas IBGE's SIDRA API (`apisidra.ibge.gov.br`) **connection-times-out from GitHub runners**, so a Brazil-via-SIDRA path falls back to FRED and yields no benefit (#54, deferred). The fetchers that work today (BLS/ONS/StatCan/ECB/ABS) are all CDN/large-institution endpoints reachable from cloud infra. So before adopting a new source, confirm it is reachable from a GitHub runner (the `update-data` workflow accepts a single-country dry-run for exactly this), and always keep the FRED series as a `fred_series` fallback.

> **Note for contributors / forks:** there are *two* network environments to keep distinct. (1) Claude Code's dev sandbox has **allowlisted egress** — most central-bank, IMF and national-stats hosts are unreachable from it, so source-touching code is validated on GitHub's runners, not locally. (2) GitHub's runners have open internet but, as above, some government APIs still refuse their cloud IPs. A source must be reachable from environment (2) to be usable in production, since that is where scheduled updates run.

When a source is stale or unreachable, the value is verified/supplemented from the official agency (see *Source Links*), and per CLAUDE.md #1 we **fix the source or defer** — we do not adopt hand-entry as a standing fallback.

---

## Central Bank Forecasts

| Institution | Data Source | Metric | Update Frequency |
|-------------|-------------|--------|------------------|
| US Federal Reserve | FOMC SEP | PCE Inflation | 4x/year |
| European Central Bank | ECB Website | HICP Inflation | 4x/year |
| Bank of England | BoE Website | CPI Inflation | 4x/year |
| Reserve Bank of Australia | RBA Website | CPI Inflation | 4x/year |
| Bank of Canada | BoC Website | CPI Inflation | 4x/year |
| Reserve Bank of New Zealand | RBNZ Website | CPI Inflation | 7x/year |
| South African Reserve Bank | SARB Website | CPI Inflation | 6x/year |
| Bank of Japan | BoJ Website | CPI Inflation | 4x/year |
| Bank of Korea | BOK Website | CPI Inflation | 4x/year |
| Monetary Authority of Singapore | MAS Website | CPI Inflation | 4x/year |
| Reserve Bank of India | RBI Website | CPI Inflation | 6x/year |
| China (PBOC) | IMF WEO | CPI Inflation | 2x/year |

**Notes:** 
- China's PBOC does not publish multi-year inflation forecasts. We use IMF projections instead.
- Singapore's MAS uses exchange rate policy (S$NEER band), not interest rates.

---

## IMF Forecasts

| Source | Dataset | Update Frequency |
|--------|---------|------------------|
| IMF World Economic Outlook | WEO Database | 2x/year (April, October) |

The IMF publishes comprehensive inflation forecasts for all countries in our coverage as part of the World Economic Outlook.

---

## Forecast History Tracking

Starting January 2026, we maintain historical records of forecast revisions:

| File | Contents | Update Frequency |
|------|----------|------------------|
| `cb_forecast_history.json` | Central bank forecast snapshots | After MPC meetings |
| `imf_forecast_history.json` | IMF WEO forecast snapshots | After WEO releases (Apr/Oct) |

This enables tracking how forecasts change over time and comparing forecast accuracy.

---

## Automation

### GitHub Actions Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| Update Inflation Data | Mon 12 PM UTC | Fetch CPI from FRED/ECB |
| Monitor & Update Data | Mon/Thu 9 AM UTC | Check FRED for new CPI data |
| Auto-Scrape CB Forecasts | Mon/Thu 10 AM UTC | Check central bank publications |
| Weekly Alert | Mon 1 PM UTC | Summary notifications |
| Newsletter Draft | 1st of month + on CPI push | Generate Claude-powered draft |

### Anomaly Detection

Both the manual entry path (`update_cpi.py`) and the historical fetcher (`fetch_historical_cpi.py`) run two checks on each new value:

- **Step threshold (1.0pp):** any month-over-month YoY change > 1pp is flagged as anomalous. Backfill points are exempt (skipped if their date is older than the existing latest) to prevent false positives when sources widen their history window — see PR #2.
- **Prior-year-same-period match:** if a new value matches the prior year's same-month value within 0.01pp, it's flagged. This catches the BR/MX 2026-01/02 failure mode where comparison-text values were captured as current readings.

In both scripts, hitting an anomaly **exits non-zero** so CI surfaces it. The auto-scraper has a related but independent **merge-gate** (`MERGE_THRESHOLD_PP = 1.0`) that routes large jumps to `cb_forecasts_draft.json` instead of auto-merging — see [`merge_into_main`](scripts/auto_scrape_cb_forecasts.py).

Per CLAUDE.md #5: when these checks fire, the fix is to investigate *why*, not to raise the threshold.

### Notification emails

Both `auto-scrape-cb-forecasts` and `update-data` send Resend emails on each successful run (PR #15, refined by #22 and #23). Subjects include the affected countries + the commit SHA; bodies embed:
- The contents of `docs/data/cb_forecasts_changes.md` for the CB pipeline (per-country before→after diffs)
- The per-country latest YoY + observation date for the FRED/ECB/BLS/ONS/StatCan pipeline
- The full commit URL so a reader can click through to the exact change

Failure-path emails (`if: failure()`) are tracked in [#28](https://github.com/jing-ny/issues/28).

### Manual Updates Required

- **Central bank forecasts:** Mostly automated (9/12) — see PROJECT_PLAN.md "Scraper status". The remaining banks (CN, IN, KR) are updated manually after MPC meetings (see CPI_UPDATE_GUIDE.md), with PBoC an explicit non-goal.
- **IMF forecasts:** April and October — `fetch_imf_forecasts.py` pulls the latest WEO.
- **CPI verification:** Monthly via `update_cpi.py` if FRED hasn't caught up. Direct-source paths (BLS for US, ONS for UK, StatCan for CA, ECB for EA) usually beat FRED to the release.

---

## Country-Specific Notes

### United States (US)
- **Oct 2025 data missing:** US government shutdown prevented BLS release

### South Africa (ZA)
- **Target Change (Nov 2025):** SARB changed inflation target from 3-6% range (4.5% midpoint) to 3% point target
- This is the first target change in 25 years

### Japan (JP)
- **FRED Series Change:** Original series JPNCPIALLMINMEI discontinued June 2021
- Now using JPNCPALTT01IXNBM (COICOP 2018 index), with COICOP 1999 as fallback
- BoJ uses fiscal year (April-March) for forecasts

### Australia (AU)
- **Monthly CPI Transition:** ABS began publishing complete monthly CPI in late 2025
- Historical data remains quarterly

### India (IN)
- RBI uses fiscal year (April-March) for forecasts
- Flexible inflation targeting framework adopted 2016
- Record-low inflation in late 2025 due to falling food prices

### Singapore (SG)
- MAS uses exchange rate policy (S$NEER band), not interest rates
- No explicit inflation target; implied ~2% for price stability
- Core inflation excludes accommodation and private transport

---

## File Structure

```
docs/data/                        # Single source of truth
├── historical_cpi.json           # CPI history for all 12 countries
├── cb_forecasts.json             # Central bank forecasts
├── imf_forecasts.json            # IMF WEO projections
├── cpi_supplements.json          # Manual supplements for FRED lag
├── weekly_snapshots.json         # Weekly data snapshots
└── history/
    ├── cb_forecast_history.json  # CB forecast revision history
    └── imf_forecast_history.json # IMF forecast revision history

scripts/                          # Data collection scripts
├── fetch_historical_cpi.py       # FRED API fetcher (all 12 countries)
├── fetch_imf_forecasts.py        # IMF API fetcher
├── auto_scrape_cb_forecasts.py   # CB publication scraper (6 banks)
├── monitor_updates.py            # Automated checker
├── send_notification.py          # Email via Resend API
├── send_weekly_alert.py          # Weekly change detection + email
└── generate_newsletter.py        # Claude API newsletter draft generation

# Manual update tools (repo root)
├── update.sh                     # One-command update tool (cpi/forecast/imf/status)
├── update_cpi.py                 # Single-value CPI updates
├── batch_update_cpi.py           # Multi-country batch updates
└── CPI_UPDATE_GUIDE.md           # Update procedures and sources
```

---

## Limitations

1. **Data Timeliness:** FRED data may lag official releases; we supplement manually when needed
2. **Central Bank Forecasts:** Most require manual updates; not all banks provide multi-year projections
3. **Methodology Differences:** Countries use slightly different CPI baskets and methodologies
4. **Revisions:** Historical data may be revised by statistical agencies after initial release

---

## Source Links

### Statistical Agencies
- **US BLS:** https://www.bls.gov/cpi/
- **Eurostat:** https://ec.europa.eu/eurostat/web/hicp
- **UK ONS:** https://www.ons.gov.uk/economy/inflationandpriceindices
- **Statistics Canada:** https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes
- **ABS:** https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/
- **Stats NZ:** https://www.stats.govt.nz/indicators/consumers-price-index-cpi/
- **Stats SA:** https://www.statssa.gov.za/
- **Japan MIC:** https://www.stat.go.jp/english/data/cpi/
- **China NBS:** https://www.stats.gov.cn/english/
- **India MOSPI:** https://www.mospi.gov.in/
- **KOSTAT:** https://kostat.go.kr/
- **SingStat:** https://www.singstat.gov.sg/

### Data APIs
- **FRED:** https://fred.stlouisfed.org/
- **IMF WEO:** https://www.imf.org/en/Publications/WEO
