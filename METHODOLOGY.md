# Methodology

Technical documentation for the Inflation Monitor dashboard.

**Last Updated:** March 24, 2026

---

## Overview

This project fetches official inflation statistics and central bank forecasts from public APIs and official sources, stores them in JSON files, and displays them on a static dashboard hosted via GitHub Pages.

All data is stored in `docs/data/` as the single source of truth.

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
| 🇯🇵 Japan | FRED (JPNCPALTT01GYM659N) | [MIC](https://www.stat.go.jp/english/data/cpi/) | Monthly |
| 🇨🇳 China | FRED (CHNCPIALLMINMEI) | [NBS](https://www.stats.gov.cn/english/) | Monthly |
| 🇮🇳 India | FRED (INDCPIALLMINMEI) | [MOSPI](https://www.mospi.gov.in/) | Monthly |
| 🇰🇷 South Korea | FRED (KORCPIALLMINMEI) | [KOSTAT](https://kostat.go.kr/) | Monthly |
| 🇸🇬 Singapore | FRED (SGPCPIALLMINMEI) | [SingStat](https://www.singstat.gov.sg/) | Monthly |
| 🇻🇪 Venezuela | FRED (FPCPITOTLZGVEN) | [BCV](https://www.bcv.org.ve/) | Monthly |

*Australia transitioned to monthly CPI in late 2025. Historical data is quarterly.

**Notes:**
- All series measure **headline CPI (All Items)** year-over-year percentage change
- FRED OECD series use base year 2015=100
- US BLS series uses base year 1982-84=100
- Japan series changed from JPNCPIALLMINMEI (discontinued Jun 2021) to JPNCPALTT01GYM659N (COICOP 2018)
- Venezuela data reliability varies; post-hyperinflation period only (2022+)

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

### FRED Data Lag Issue

FRED's OECD series for international countries often lag official releases by 1-12 months:

| Country | Typical Lag | Workaround |
|---------|-------------|------------|
| South Africa | 6-12 months | Manual supplement from Stats SA |
| UK, Canada | 1-2 months | Manual supplement from ONS/StatCan |
| Australia | 1-2 quarters | ABS now publishes monthly |
| New Zealand | 1-2 quarters | Quarterly release schedule |
| Venezuela | 6-12 months | IMF data used |

When FRED data is stale, we verify and supplement with official data from the sources listed above.

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
| Venezuela (BCV) | IMF WEO | CPI Inflation | 2x/year |

**Notes:** 
- China's PBOC does not publish multi-year inflation forecasts. We use IMF projections instead.
- Venezuela's BCV does not publish reliable forecasts. We use IMF projections instead.
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
| Monitor & Update Data | Mon/Thu 9 AM UTC | Check FRED for new CPI data |
| Auto-Scrape CB Forecasts | Mon/Thu 10 AM UTC | Check central bank publications |
| Weekly Alert | Mon 1 PM UTC | Summary notifications |

### Manual Updates Required

- **Central bank forecasts:** After MPC meetings (see MAINTENANCE.md)
- **IMF forecasts:** April and October
- **CPI verification:** Monthly, using `update_cpi.py`

---

## Country-Specific Notes

### United States (US)
- **Oct 2025 data missing:** US government shutdown prevented BLS release

### South Africa (ZA)
- **Target Change (Nov 2025):** SARB changed inflation target from 3-6% range (4.5% midpoint) to 3% point target
- This is the first target change in 25 years

### Japan (JP)
- **FRED Series Change:** Original series JPNCPIALLMINMEI discontinued June 2021
- Now using JPNCPALTT01GYM659N (COICOP 2018 classification)
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

### Venezuela (VE)
- Post-hyperinflation period only (2022+)
- Hyperinflation 2016-2021 peaked at 1,000,000%+ in 2018
- No formal inflation targeting framework (`target: null` in data)
- Data reliability uncertain; IMF projections used for forecasts

---

## File Structure

```
docs/data/                        # Single source of truth
├── historical_cpi.json           # CPI history for all 13 countries
├── cb_forecasts.json             # Central bank forecasts
├── imf_forecasts.json            # IMF WEO projections
├── cpi_supplements.json          # Manual supplements for FRED lag
├── weekly_snapshots.json         # Weekly data snapshots
└── history/
    ├── cb_forecast_history.json  # CB forecast revision history
    └── imf_forecast_history.json # IMF forecast revision history

scripts/                          # Data collection scripts
├── fetch_historical_cpi.py       # FRED API fetcher
├── fetch_imf_forecasts.py        # IMF API fetcher
├── auto_scrape_cb_forecasts.py   # CB publication scraper
├── monitor_updates.py            # Automated checker
└── send_notification.py          # Email notifications

# Manual update tools (repo root)
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
5. **Venezuela:** Data reliability uncertain due to economic instability

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
- **Venezuela BCV:** https://www.bcv.org.ve/

### Data APIs
- **FRED:** https://fred.stlouisfed.org/
- **IMF WEO:** https://www.imf.org/en/Publications/WEO
