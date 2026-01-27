# Methodology

Technical documentation for the Inflation Monitor dashboard.

**Last Updated:** January 27, 2026

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
| 🇯🇵 Japan | JPNCPALTT01GYM659N | Monthly | Statistics Bureau via OECD | FRED API |
| 🇰🇷 South Korea | KORCPIALLMINMEI | Monthly | KOSTAT via OECD | FRED API |
| 🇸🇬 Singapore | SGPCPIALLMINMEI | Monthly | DOS via OECD | FRED API |
| 🇮🇳 India | INDCPIALLMINMEI | Monthly | MOSPI via OECD | FRED API |
| 🇨🇳 China | CHNCPIALLMINMEI | Monthly | NBS via OECD | FRED API |
| 🇻🇪 Venezuela | FPCPITOTLZGVEN | Annual | BCV / World Bank | FRED API |

*Australia transitioned to monthly CPI in October 2025. Historical data is quarterly.

**Notes:**
- All series measure **headline CPI (All Items)** year-over-year percentage change
- FRED OECD series use base year 2015=100
- US BLS series uses base year 1982-84=100
- Japan series changed from JPNCPIALLMINMEI (discontinued Jun 2021) to JPNCPALTT01GYM659N (COICOP 2018)
- Venezuela data reliability varies; post-hyperinflation period only (2022+)

### FRED Data Lag Issue

FRED's OECD series for international countries often lag official releases by 1-12 months:

| Country | Typical Lag | Workaround |
|---------|-------------|------------|
| South Africa | 6-12 months | Manual supplement from Stats SA |
| UK, Canada | 1-2 months | Manual supplement from ONS/StatCan |
| Australia | 1-2 quarters | ABS now publishes monthly |
| New Zealand | 1-2 quarters | Quarterly release schedule |
| Venezuela | 6-12 months | IMF data used |

When FRED data is stale, we supplement with official data from:
- **Stats SA:** https://www.statssa.gov.za/?cat=33
- **ONS:** https://www.ons.gov.uk/economy/inflationandpriceindices
- **Statistics Canada:** https://www150.statcan.gc.ca/n1/daily-quotidien/
- **ABS:** https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/

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
- Singapore's MAS uses exchange rate policy (S$NEER), not interest rates.

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

### GitHub Actions Workflow

**Schedule:** Monday & Thursday at 9 AM UTC

**What it does:**
1. Checks FRED API for new CPI data
2. Auto-commits updates if new data found
3. Sends email alerts via Resend for:
   - New data updates
   - Stale data warnings (>75 days old)
   - CB meeting reminders
   - IMF WEO release reminders (Apr/Oct)

### Manual Updates Required

- **Central bank forecasts:** After MPC meetings
- **IMF forecasts:** April and October

See `MAINTENANCE.md` for detailed instructions.

---

## Country-Specific Notes

### South Africa (ZA)
- **Target Change (Nov 2025):** SARB changed inflation target from 3-6% range (4.5% midpoint) to 3% ±1pp (2-4% range)
- This is the first target change in 25 years

### Japan (JP)
- **FRED Series Change:** Original series JPNCPIALLMINMEI discontinued June 2021
- Now using JPNCPALTT01GYM659N (COICOP 2018 classification)
- BoJ uses fiscal year (April-March) for forecasts

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
docs/data/
├── historical_cpi.json       # 10-year CPI history per country
├── cb_forecasts.json         # Central bank forecasts
├── imf_forecasts.json        # IMF WEO projections
└── history/
    ├── cb_forecast_history.json   # CB forecast revision history
    └── imf_forecast_history.json  # IMF forecast revision history

scripts/
├── monitor_updates.py        # Automated FRED checker
└── send_notification.py      # Email notifications via Resend
```

---

## Limitations

1. **Data Timeliness:** FRED data may lag official releases; we supplement manually when needed
2. **Central Bank Forecasts:** Most require manual updates; not all banks provide multi-year projections
3. **Methodology Differences:** Countries use slightly different CPI baskets and methodologies
4. **Revisions:** Historical data may be revised by statistical agencies after initial release
5. **Venezuela:** Data reliability uncertain due to economic instability
6. **FRED API Compatibility:** Japan and Singapore series don't support automated percent-change calculation

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
- **Japan Statistics Bureau:** https://www.stat.go.jp/english/data/cpi/
- **Korea KOSTAT:** https://kostat.go.kr/en/
- **Singapore DOS:** https://www.singstat.gov.sg/
- **India MOSPI:** https://www.mospi.gov.in/
- **China NBS:** http://www.stats.gov.cn/english/
- **Venezuela BCV:** https://www.bcv.org.ve/

### Central Banks
- **Federal Reserve:** https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- **ECB:** https://www.ecb.europa.eu/pub/projections/html/index.en.html
- **Bank of England:** https://www.bankofengland.co.uk/monetary-policy-report
- **RBA:** https://www.rba.gov.au/publications/smp/
- **Bank of Canada:** https://www.bankofcanada.ca/publications/mpr/
- **RBNZ:** https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement
- **SARB:** https://www.resbank.co.za/en/home/publications/publication-detail-pages/statements/monetary-policy-statements
- **Bank of Japan:** https://www.boj.or.jp/en/mopo/outlook/
- **Bank of Korea:** https://www.bok.or.kr/eng/main/main.do
- **MAS:** https://www.mas.gov.sg/monetary-policy
- **RBI:** https://www.rbi.org.in/

### APIs & Data
- **FRED API:** https://fred.stlouisfed.org/docs/api/
- **IMF WEO:** https://www.imf.org/external/datamapper/PCPIPCH@WEO

---

*For architecture and maintenance details, see PROJECT_PLAN.md and MAINTENANCE.md*
