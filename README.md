# Inflation Monitor

A simple dashboard tracking official inflation data and central bank forecasts across major economies.

**🔗 [View Live Dashboard](https://jing-ny.github.io/inflation-dashboard/)**

---

## What This Shows

### Current Inflation Rates
Year-over-year consumer price index (CPI) changes for 8 major economies:
- 🇺🇸 United States
- 🇪🇺 Euro Area
- 🇬🇧 United Kingdom
- 🇨🇦 Canada
- 🇦🇺 Australia
- 🇳🇿 New Zealand
- 🇿🇦 South Africa
- 🇨🇳 China

### 10-Year Historical Trends
Interactive charts showing how inflation evolved through:
- Pre-pandemic stability (2015-2019)
- COVID-19 disruption (2020)
- Post-pandemic inflation surge (2021-2022)
- Current normalization period (2023-present)

### Central Bank Forecasts
Official inflation projections from major central banks including the Federal Reserve, ECB, Bank of England, and others.

---

## Data Sources & Freshness

All data comes from official government statistics and central bank publications. However, **data freshness varies significantly by source**:

### Current Status (as of Jan 2026)

| Country | Latest Data | Lag | Source | API |
|---------|-------------|-----|--------|-----|
| 🇺🇸 US | Dec 2025 | ✅ Current | Bureau of Labor Statistics | FRED direct |
| 🇪🇺 Euro Area | Dec 2025 | ✅ Current | Eurostat | ECB SDMX |
| 🇬🇧 UK | Mar 2025 | ⚠️ ~9 months | ONS via OECD | FRED OECD |
| 🇨🇦 Canada | Mar 2025 | ⚠️ ~9 months | StatCan via OECD | FRED OECD |
| 🇨🇳 China | Apr 2025 | ⚠️ ~8 months | NBS via OECD | FRED OECD |
| 🇦🇺 Australia | Q1 2025 | ⚠️ ~3 quarters | ABS via OECD | FRED OECD |
| 🇳🇿 New Zealand | Q1 2025 | ⚠️ ~3 quarters | Stats NZ via OECD | FRED OECD |
| 🇿🇦 South Africa | Jan 2025 | ⚠️ ~12 months | Stats SA via OECD | FRED OECD |

### Why the Lag?

FRED's OECD series are convenient but have significant publication delays (OECD aggregates data from national sources with 1-9 month lag). Direct national APIs provide current data but require more complex integration.

---

## Improvement Priorities

### P0: Data Freshness (Critical)
Switching to direct national APIs would provide current data:

| Country | Target API | Status | Notes |
|---------|------------|--------|-------|
| 🇬🇧 UK | [ONS API](https://developer.ons.gov.uk/) | 🔄 To do | Series D7G7 = CPI Annual Rate |
| 🇨🇦 Canada | [StatCan API](https://www.statcan.gc.ca/en/developers/wds) | 🔄 To do | Table 18-10-004-01 |
| 🇦🇺 Australia | [ABS API](https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis) | 🔄 To do | New CPI_M dataflow (Nov 2025) |
| 🇿🇦 South Africa | [Stats SA](http://www.statssa.gov.za/) | 🔄 To do | No public API, may need scraping |
| 🇨🇳 China | [NBS](https://www.stats.gov.cn/) | 🔄 To do | No public API, may need scraping |
| 🇯🇵 Japan | [e-Stat API](https://www.e-stat.go.jp/en/api/) | 🔄 To do | Complex auth, would re-add Japan |

### P1: Central Bank Forecasts
- Forecasts currently require manual updates
- Could automate with PDF parsing or official APIs where available
- Priority: Fed, ECB, BoE, RBA

**Forecast Publication Schedule:**

| Central Bank | Frequency | Months | Source |
|--------------|-----------|--------|--------|
| 🇺🇸 Fed (FOMC) | Quarterly | Mar, Jun, Sep, Dec | [SEP Projections](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) |
| 🇪🇺 ECB | Quarterly | Mar, Jun, Sep, Dec | [Staff Projections](https://www.ecb.europa.eu/pub/projections/html/index.en.html) |
| 🇬🇧 BoE | Quarterly | Feb, May, Aug, Nov | [Monetary Policy Report](https://www.bankofengland.co.uk/monetary-policy-report) |
| 🇦🇺 RBA | Quarterly | Feb, May, Aug, Nov | [Statement on Monetary Policy](https://www.rba.gov.au/publications/smp/) |
| 🇳🇿 RBNZ | Quarterly | Feb, May, Aug, Nov | [Monetary Policy Statement](https://www.rbnz.govt.nz/monetary-policy/monetary-policy-statement) |
| 🇿🇦 SARB | Bi-monthly | 6x per year | [MPC Statements](https://www.resbank.co.za/en/home/publications/statements/monetary-policy-statements) |
| 🇨🇦 BoC | Quarterly | Jan, Apr, Jul, Oct | [Monetary Policy Report](https://www.bankofcanada.ca/publications/mpr/) |

### P2: Infrastructure
- Supabase backend for forecast history tracking
- Email subscription for material changes (≥0.3pp moves)
- Data freshness warnings in UI
- Error monitoring and alerts

---

## Technical Details

For detailed methodology including calculation methods, data transformations, and source citations, see [METHODOLOGY.md](METHODOLOGY.md).

### Running the Data Fetch

```bash
# Requires Python 3.8+ and requests library
pip install requests

# Set FRED API key (get free key at https://fred.stlouisfed.org/docs/api/api_key.html)
export FRED_API_KEY=your_key_here

# Fetch latest data
python3 scripts/fetch_historical_cpi.py

# Copy to docs for GitHub Pages
cp data/historical_cpi.json docs/data/
```

---

## Updates

Data is updated weekly. The dashboard reflects the latest available official releases, subject to the source lag noted above.

---

## Disclaimer

This is a personal research tool for informational purposes only. It is not financial advice. Always verify data with primary sources before making any decisions.

---

## Contact

Questions or suggestions? [Open an issue](https://github.com/jing-ny/inflation-dashboard/issues) on GitHub.
