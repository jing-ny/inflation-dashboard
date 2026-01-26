# Methodology

Technical documentation for the Inflation Monitor dashboard.

---

## Overview

This project fetches official inflation statistics and central bank forecasts from public APIs, stores them in a database, and displays them on a static dashboard.

---

## Data Collection

### Actual Inflation (CPI)

| Country | Series ID | Frequency | Original Source | API Used |
|---------|-----------|-----------|-----------------|----------|
| 🇺🇸 United States | CUSR0000SA0 | Monthly | Bureau of Labor Statistics | BLS API |
| 🇬🇧 United Kingdom | GBRCPIALLMINMEI | Monthly | ONS via OECD | FRED API |
| 🇩🇪 Germany | DEUCPIALLMINMEI | Monthly | Destatis via OECD | FRED API |
| 🇪🇺 Euro Area | ICP.M.U2.N.000000.4.ANR | Monthly | Eurostat | ECB API |
| 🇦🇺 Australia | AUSCPIALLQINMEI | Quarterly | ABS via OECD | FRED API |
| 🇳🇿 New Zealand | NZLCPIALLQINMEI | Quarterly | Stats NZ via OECD | FRED API |
| 🇿🇦 South Africa | ZAFCPIALLMINMEI | Monthly | Stats SA via OECD | FRED API |

**Notes:**
- All series measure **headline CPI (All Items)**
- FRED series use OECD data with base year 2015=100
- US BLS uses base year 1982-84=100
- Australia and New Zealand report quarterly (official release cadence)
- South Africa FRED data may lag official Stats SA releases by several months

### Central Bank Forecasts

| Institution | Data Type | Series/Source | Frequency |
|-------------|-----------|---------------|-----------|
| US Federal Reserve | FOMC PCE projections | PCECTPIMD (FRED) | 4x/year |
| Cleveland Fed | 1-Year inflation expectations | EXPINF1YR (FRED) | Monthly |
| European Central Bank | Staff projections | ECB website | 4x/year |
| European Central Bank | Survey of Professional Forecasters | SPF dataset (ECB API) | Quarterly |
| Bank of England | MPC projections | Monetary Policy Report | 4x/year |
| Reserve Bank of Australia | Staff forecasts | Statement on Monetary Policy | 4x/year |

---

## Calculation Methods

### Year-over-Year (YoY) Inflation

```
YoY % = ((CPI_current / CPI_12months_ago) - 1) × 100
```

For quarterly data (AU, NZ):
```
YoY % = ((CPI_current_quarter / CPI_same_quarter_last_year) - 1) × 100
```

### Change Indicators

- **Up** (red): Current rate > Previous rate by ≥ 0.1pp
- **Down** (green): Current rate < Previous rate by ≥ 0.1pp  
- **Flat** (gray): Change < 0.1pp

### Color Coding (vs Target)

- **High** (red): > 2pp above target
- **Medium** (amber): 0.5-2pp above target
- **Low** (green): > 0.5pp below target
- **Neutral** (black): Within ±0.5pp of target

---

## API Details

### FRED API (Federal Reserve Economic Data)

- **Endpoint**: `https://api.stlouisfed.org/fred/series/observations`
- **Authentication**: Free API key required
- **Rate Limit**: 120 requests per minute
- **Documentation**: https://fred.stlouisfed.org/docs/api/fred/

### ECB Data Portal (SDMX)

- **Endpoint**: `https://data-api.ecb.europa.eu/service/data`
- **Authentication**: None required
- **Format**: CSV (`format=csvdata`) recommended
- **Documentation**: https://data.ecb.europa.eu/help/api/overview

### BLS API

- **Endpoint**: `https://api.bls.gov/publicAPI/v2/timeseries/data/`
- **Authentication**: API key recommended (higher rate limits)
- **Documentation**: https://www.bls.gov/developers/

---

## Data Pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Official   │     │   Python    │     │  Supabase   │     │   Static    │
│    APIs     │────▶│  Fetchers   │────▶│  Database   │────▶│  Dashboard  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     BLS              fetch_us.py         PostgreSQL          index.html
     FRED             fetch_uk.py         (planned)           Chart.js
     ECB              fetch_ecb.py
```

### Scripts

| Script | Purpose |
|--------|---------|
| `fetch_us.py` | US CPI from BLS |
| `fetch_uk.py` | UK CPI from FRED |
| `fetch_de.py` | Germany CPI from FRED |
| `fetch_nz.py` | New Zealand CPI from FRED |
| `fetch_au.py` | Australia CPI from FRED |
| `fetch_za.py` | South Africa CPI from FRED |
| `fetch_us_fed_forecast.py` | FOMC projections from FRED |
| `fetch_ecb_forecast.py` | ECB SPF and HICP from ECB API |

---

## Inflation Targets

| Central Bank | Target | Notes |
|--------------|--------|-------|
| Federal Reserve | 2.0% | PCE inflation, symmetric |
| European Central Bank | 2.0% | HICP, symmetric |
| Bank of England | 2.0% | CPI, symmetric (±1pp letter trigger) |
| Reserve Bank of Australia | 2-3% | Trimmed mean, range target |
| Reserve Bank of New Zealand | 1-3% | CPI, midpoint focus at 2% |
| South African Reserve Bank | 3-6% | CPI, midpoint objective 4.5% |

---

## Known Limitations

1. **Data Lag**: FRED/OECD data may lag primary sources by days/weeks
2. **South Africa**: FRED data lags Stats SA by several months
3. **Forecasts**: BoE, RBA, RBNZ forecasts currently hardcoded (no API available)
4. **Historical Data**: Dashboard uses simulated 10-year history (to be replaced with actual data)

---

## Future Improvements

- [ ] Replace simulated historical data with actual series
- [ ] Add Supabase integration for data storage
- [ ] Implement automated weekly updates via Vercel cron
- [ ] Add Japan, Canada, Switzerland
- [ ] Parse BoE/RBA/RBNZ PDFs for automated forecast updates

---

## Tech Stack

- **Data Fetching**: Python 3, requests
- **Database**: Supabase (PostgreSQL) - planned
- **Frontend**: Static HTML, Chart.js
- **Hosting**: GitHub Pages
- **Automation**: Vercel Serverless Functions - planned

---

## Environment Variables

```bash
FRED_API_KEY=your_key_here      # Get free at fred.stlouisfed.org
SUPABASE_URL=your_url           # Optional, for database
SUPABASE_KEY=your_key           # Optional, for database
```

---

## License

MIT License - See repository for details.
