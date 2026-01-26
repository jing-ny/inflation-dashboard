# Methodology

Technical documentation for the Inflation Monitor dashboard.

**Last Updated:** January 26, 2026

---

## Overview

This project fetches official inflation statistics and central bank forecasts from public APIs and official sources, stores them in JSON files, and displays them on a static dashboard hosted via GitHub Pages.

---

## Data Collection

### Actual Inflation (CPI)

| Country | Series ID | Frequency | Original Source | API Used |
|---------|-----------|-----------|-----------------|----------|
| 🇺🇸 United States | CPIAUCSL | Monthly | Bureau of Labor Statistics | FRED API |
| 🇪🇺 Euro Area | CP0000EZ19M086NEST | Monthly | Eurostat | FRED API |
| 🇬🇧 United Kingdom | GBRCPIALLMINMEI | Monthly | ONS via OECD | FRED API |
| 🇨🇦 Canada | CANCPIALLMINMEI | Monthly | Statistics Canada via OECD | FRED API |
| 🇦🇺 Australia | AUSCPIALLQINMEI | Quarterly* | ABS via OECD | FRED API |
| 🇳🇿 New Zealand | NZLCPIALLQINMEI | Quarterly | Stats NZ via OECD | FRED API |
| 🇿🇦 South Africa | ZAFCPIALLMINMEI | Monthly | Stats SA via OECD | FRED API |
| 🇨🇳 China | CHNCPIALLMINMEI | Monthly | NBS via OECD | FRED API |

*Australia transitioned to monthly CPI in October 2025. Historical data is quarterly.

**Notes:**
- All series measure **headline CPI (All Items)** year-over-year percentage change
- FRED OECD series use base year 2015=100
- US BLS series uses base year 1982-84=100

### FRED Data Lag Issue

FRED's OECD series for international countries often lag official releases by 1-12 months:

| Country | Typical Lag | Workaround |
|---------|-------------|------------|
| South Africa | 6-12 months | Manual supplement from Stats SA |
| UK, Canada | 1-2 months | Manual supplement from ONS/StatCan |
| Australia | 1-2 quarters | ABS now publishes monthly |
| New Zealand | 1-2 quarters | Quarterly release schedule |

When FRED data is stale, we supplement with official data from:
- **Stats SA:** https://www.statssa.gov.za/?cat=33
- **ONS:** https://www.ons.gov.uk/economy/inflationandpriceindices
- **Statistics Canada:** https://www150.statcan.gc.ca/n1/daily-quotidien/
- **ABS:** https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/

---

## Central Bank Forecasts

| Institution | Data Source | Metric | Update Frequency |
|-------------|-------------|--------|------------------|
| US Federal Reserve | FRED API (PCECTPIMD) | PCE Inflation | 4x/year (FOMC SEP) |
| Cleveland Fed | FRED API (EXPINF1YR) | 1-Year CPI Expectations | Monthly |
| European Central Bank | ECB Website | HICP Inflation | 4x/year (Staff Projections) |
| Bank of England | BoE Website | CPI Inflation | 4x/year (MPR) |
| Reserve Bank of Australia | RBA Website | CPI Inflation | 4x/year (SoMP) |
| Bank of Canada | BoC Website | CPI Inflation | 4x/year (MPR) |
| Reserve Bank of New Zealand | RBNZ Website | CPI Inflation | 7x/year (MPS) |
| South African Reserve Bank | SARB Website | CPI Inflation | 6x/year (MPC) |
| China (PBOC) | IMF WEO | CPI Inflation | 2x/year |

**Note:** China's PBOC does not publish multi-year inflation forecasts. We use IMF projections instead.

### Forecast Data Sources

**Automated (via FRED API):**
- US FOMC median PCE projections
- Cleveland Fed inflation expectations model

**Manual (from official publications):**
- ECB Staff Macroeconomic Projections
- BoE Monetary Policy Report
- RBA Statement on Monetary Policy
- BoC Monetary Policy Report
- RBNZ Monetary Policy Statement
- SARB MPC Statement

---

## IMF Forecasts

| Source | Dataset | Update Frequency |
|--------|---------|------------------|
| IMF World Economic Outlook | WEO Database API | 2x/year (April, October) |

The IMF publishes comprehensive inflation forecasts for all countries in our coverage as part of the World Economic Outlook. We fetch:
- Current year projection
- Next year projection
- 2-year ahead projection (where available)

---

## Data Processing

### Year-over-Year Calculation

For CPI index values, YoY inflation is calculated as:

```
YoY% = ((Current Month Index / Same Month Last Year Index) - 1) × 100
```

Most FRED series already provide YoY percentage change directly.

### Data Validation

Before displaying data:
1. Check that values are within reasonable bounds (-5% to +20% for most countries)
2. Verify dates are sequential with no gaps
3. Cross-reference latest values with official sources

---

## Update Schedule

| Data Type | Automated | Frequency |
|-----------|-----------|-----------|
| Historical CPI | Yes (GitHub Actions) | Weekly |
| IMF Forecasts | Yes (GitHub Actions) | Weekly (changes 2x/year) |
| CB Forecasts (Fed) | Yes (GitHub Actions) | Weekly |
| CB Forecasts (Others) | No | After policy meetings |
| CPI Supplements | No | As needed when FRED lags |

### GitHub Actions Workflow

The automated workflow runs weekly:
1. Fetches latest CPI data from FRED
2. Fetches latest IMF forecasts
3. Fetches Fed/Cleveland Fed forecasts from FRED
4. Copies updated JSON files to docs/data/
5. Commits and pushes changes

---

## File Structure

```
docs/data/
├── historical_cpi.json    # 10-year CPI history per country
├── cb_forecasts.json      # Central bank forecasts
└── imf_forecasts.json     # IMF WEO projections

scripts/
├── fetch_historical_cpi.py   # FRED API → historical_cpi.json
├── fetch_cb_forecasts.py     # Hybrid API + manual → cb_forecasts.json
└── fetch_imf_forecasts.py    # IMF API → imf_forecasts.json

data/
├── cpi_supplements.json      # Manual data for FRED lag
└── (copies of above for backup)
```

---

## JSON Schema

### historical_cpi.json

```json
{
  "_metadata": {
    "last_updated": "2026-01-26",
    "description": "Historical CPI inflation data"
  },
  "US": {
    "name": "United States",
    "flag": "🇺🇸",
    "target": 2.0,
    "latest": {"date": "2025-12", "value": 2.9},
    "previous": {"date": "2025-11", "value": 2.7},
    "history": [
      {"date": "2015-01", "value": -0.1},
      ...
    ]
  }
}
```

### cb_forecasts.json

```json
{
  "_metadata": {
    "last_updated": "2026-01-26"
  },
  "forecasts": [
    {
      "bank": "Federal Reserve (FOMC)",
      "country": "US",
      "metric": "PCE Inflation",
      "source": "Summary of Economic Projections",
      "source_date": "Dec 2025",
      "projections": [
        {"year": "2025", "value": 2.8},
        {"year": "2026", "value": 2.4},
        {"year": "2027", "value": 2.1}
      ]
    }
  ]
}
```

### imf_forecasts.json

```json
{
  "_metadata": {
    "source": "IMF World Economic Outlook",
    "release": "October 2025",
    "last_updated": "2026-01-26"
  },
  "US": {
    "2025": 2.8,
    "2026": 2.3,
    "2027": 2.1
  }
}
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
- **Australia ABS:** https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation
- **Stats NZ:** https://www.stats.govt.nz/indicators/consumers-price-index-cpi/
- **Stats SA:** https://www.statssa.gov.za/?cat=33
- **China NBS:** http://www.stats.gov.cn/english/

### Central Banks
- **Federal Reserve:** https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- **ECB:** https://www.ecb.europa.eu/pub/projections/html/index.en.html
- **Bank of England:** https://www.bankofengland.co.uk/monetary-policy-report
- **RBA:** https://www.rba.gov.au/publications/smp/
- **Bank of Canada:** https://www.bankofcanada.ca/publications/mpr/
- **RBNZ:** https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement
- **SARB:** https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements

### APIs
- **FRED API:** https://fred.stlouisfed.org/docs/api/
- **IMF WEO API:** https://www.imf.org/en/Publications/WEO

---

*For architecture and project management details, see PROJECT_PLAN.md*
