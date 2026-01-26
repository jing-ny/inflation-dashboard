# Inflation Monitor (MVP)

A lightweight, research-oriented dashboard to monitor official inflation data
and central bank inflation forecasts across selected countries.

This project is designed to be:
- Low-frequency (weekly updates)
- Free / near-zero cost
- Fully based on official or quasi-official sources
- Easy to maintain by a non-professional developer

## Covered Countries

| Country | Script | Series | Frequency | Source |
|---------|--------|--------|-----------|--------|
| 🇺🇸 United States | `fetch_us.py` | CUSR0000SA0 | Monthly | BLS API |
| 🇬🇧 United Kingdom | `fetch_uk.py` | GBRCPIALLMINMEI | Monthly | FRED (OECD/ONS) |
| 🇩🇪 Germany | `fetch_de.py` | DEUCPIALLMINMEI | Monthly | FRED (OECD/Destatis) |
| 🇳🇿 New Zealand | `fetch_nz.py` | NZLCPIALLQINMEI | Quarterly | FRED (OECD/Stats NZ) |
| 🇦🇺 Australia | `fetch_au.py` | AUSCPIALLQINMEI | Quarterly | FRED (OECD/ABS) |

All series are **headline CPI (All Items)** with base year 2015=100 (except US which uses 1982-84=100).

## Data Sources

### US CPI
- **Source**: Bureau of Labor Statistics (BLS)
- **Series**: CUSR0000SA0 (CPI-U All Urban Consumers)
- **Frequency**: Monthly
- **API**: https://api.bls.gov/publicAPI/v2/timeseries/data/

### UK CPI
- **Source**: FRED (Federal Reserve Economic Data)
- **Original Data**: OECD -> ONS (Office for National Statistics)
- **Series**: GBRCPIALLMINMEI
- **Frequency**: Monthly
- **Note**: FRED provides more stable API than ONS direct endpoints

### Germany CPI
- **Source**: FRED
- **Original Data**: OECD -> Destatis (Federal Statistical Office)
- **Series**: DEUCPIALLMINMEI
- **Frequency**: Monthly

### New Zealand CPI
- **Source**: FRED
- **Original Data**: OECD -> Stats NZ
- **Series**: NZLCPIALLQINMEI
- **Frequency**: Quarterly (NZ official release cadence)

### Australia CPI
- **Source**: FRED
- **Original Data**: OECD -> ABS (Australian Bureau of Statistics)
- **Series**: AUSCPIALLQINMEI
- **Frequency**: Quarterly (AU official release cadence)

## What This Project Does

- Fetches latest headline CPI from official statistical agencies
- Calculates Year-over-Year (YoY) inflation rates
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
# Fetch individual countries
python3 scripts/fetch_us.py
python3 scripts/fetch_uk.py
python3 scripts/fetch_de.py
python3 scripts/fetch_nz.py
python3 scripts/fetch_au.py
```

## Environment Variables

Create a `.env.local` file in the project root:

```
FRED_API_KEY=your_fred_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Get a free FRED API key at: https://fred.stlouisfed.org/docs/api/api_key.html

---

This is a research tool, not a trading system.
