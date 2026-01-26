# Inflation Monitor (MVP)

A lightweight, research-oriented dashboard to monitor official inflation data
and central bank inflation forecasts across selected countries.

This project is designed to be:
- Low-frequency (weekly updates)
- Free / near-zero cost
- Fully based on official or quasi-official sources
- Easy to maintain by a non-professional developer

## Covered Countries

### Actual CPI Data

| Country | Script | Series | Frequency | Source |
|---------|--------|--------|-----------|--------|
| 🇺🇸 United States | `fetch_us.py` | CUSR0000SA0 | Monthly | BLS API |
| 🇬🇧 United Kingdom | `fetch_uk.py` | GBRCPIALLMINMEI | Monthly | FRED (OECD/ONS) |
| 🇩🇪 Germany | `fetch_de.py` | DEUCPIALLMINMEI | Monthly | FRED (OECD/Destatis) |
| 🇿🇦 South Africa | `fetch_za.py` | ZAFCPIALLMINMEI | Monthly | FRED (OECD/Stats SA) |
| 🇳🇿 New Zealand | `fetch_nz.py` | NZLCPIALLQINMEI | Quarterly | FRED (OECD/Stats NZ) |
| 🇦🇺 Australia | `fetch_au.py` | AUSCPIALLQINMEI | Quarterly | FRED (OECD/ABS) |

All series are **headline CPI (All Items)** with base year 2015=100 (except US which uses 1982-84=100).

### Central Bank Inflation Forecasts

| Region | Script | Data Type | Source | Frequency |
|--------|--------|-----------|--------|-----------|
| 🇺🇸 US Fed | `fetch_us_fed_forecast.py` | FOMC PCE projections | FRED API | 4x/year |
| 🇺🇸 US Fed | `fetch_us_fed_forecast.py` | Cleveland Fed 1-yr expectations | FRED API | Monthly |
| 🇪🇺 Euro Area | `fetch_ecb_forecast.py` | SPF inflation expectations | ECB API | Quarterly |

## Data Sources

### Actual Inflation (CPI)

#### US CPI
- **Source**: Bureau of Labor Statistics (BLS)
- **Series**: CUSR0000SA0 (CPI-U All Urban Consumers)
- **Frequency**: Monthly
- **API**: https://api.bls.gov/publicAPI/v2/timeseries/data/

#### UK CPI
- **Source**: FRED (Federal Reserve Economic Data)
- **Original Data**: OECD -> ONS (Office for National Statistics)
- **Series**: GBRCPIALLMINMEI
- **Frequency**: Monthly
- **Note**: FRED provides more stable API than ONS direct endpoints

#### Germany CPI
- **Source**: FRED
- **Original Data**: OECD -> Destatis (Federal Statistical Office)
- **Series**: DEUCPIALLMINMEI
- **Frequency**: Monthly

#### South Africa CPI
- **Source**: FRED
- **Original Data**: OECD -> Stats SA (Statistics South Africa)
- **Series**: ZAFCPIALLMINMEI
- **Frequency**: Monthly
- **Note**: FRED data may lag behind Stats SA by several months (see Future Improvements)

#### New Zealand CPI
- **Source**: FRED
- **Original Data**: OECD -> Stats NZ
- **Series**: NZLCPIALLQINMEI
- **Frequency**: Quarterly (NZ official release cadence)

#### Australia CPI
- **Source**: FRED
- **Original Data**: OECD -> ABS (Australian Bureau of Statistics)
- **Series**: AUSCPIALLQINMEI
- **Frequency**: Quarterly (AU official release cadence)

### Central Bank Forecasts

#### US Federal Reserve (FOMC)
- **Source**: FRED API
- **Series**: 
  - `PCECTPIMD` - FOMC PCE Inflation Median Projection (from dot plot meetings)
  - `EXPINF1YR` - Cleveland Fed 1-Year Expected Inflation (model-based)
  - `PCECTPIMDLR` - FOMC Longer-Run Inflation Target
- **Frequency**: FOMC projections 4x/year; Cleveland Fed monthly
- **Script**: `fetch_us_fed_forecast.py`

#### European Central Bank (ECB)
- **Source**: ECB Data Portal (SDMX API)
- **Data**:
  - Survey of Professional Forecasters (SPF) - inflation expectations
  - HICP actual inflation for comparison
- **Frequency**: Quarterly
- **Script**: `fetch_ecb_forecast.py`
- **Note**: Official staff projections require parsing from ECB website

## What This Project Does

- Fetches latest headline CPI from official statistical agencies
- Calculates Year-over-Year (YoY) inflation rates
- Fetches central bank inflation forecasts and expectations
- Stores data in Supabase
- Runs weekly updates via Vercel Cron
- Detects material changes
- Sends an email notification only when changes are material

## Definition of "Material Change"

Absolute CPI change >= 0.3 percentage points compared to last snapshot.

## Tech Stack

- **Backend / Cron**: Vercel Serverless Functions
- **Database**: Supabase (Postgres)
- **Frontend**: Minimal Next.js page (optional)
- **Email**: Free-tier email service
- **Automation Assistant**: Claude

## Usage

```bash
# Fetch actual CPI data
python3 scripts/fetch_us.py
python3 scripts/fetch_uk.py
python3 scripts/fetch_de.py
python3 scripts/fetch_za.py
python3 scripts/fetch_nz.py
python3 scripts/fetch_au.py

# Fetch central bank forecasts
python3 scripts/fetch_us_fed_forecast.py
python3 scripts/fetch_ecb_forecast.py
```

## Environment Variables

Create a `.env.local` file in the project root:

```
FRED_API_KEY=your_fred_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Get a free FRED API key at: https://fred.stlouisfed.org/docs/api/api_key.html

## Future Improvements

### Data Sources
- [ ] **South Africa**: Switch to Stats SA direct API for more timely data (FRED lags by several months)
- [ ] Add more countries (e.g., Japan, Canada)

### Central Bank Forecasts (Phase 2)
- [ ] **Bank of England**: Parse Monetary Policy Report for UK inflation forecasts
- [ ] **Reserve Bank of NZ**: Parse MPS XLSX files for NZ forecasts
- [ ] **Reserve Bank of Australia**: Parse SoMP for AU forecasts
- [ ] **SA Reserve Bank**: Parse Monetary Policy Review for ZA forecasts

### Infrastructure
- [ ] Implement Supabase integration for all fetchers
- [ ] Add automated weekly cron job
- [ ] Build dashboard frontend

---

This is a research tool, not a trading system.
