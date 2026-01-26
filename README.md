# Inflation Monitor (MVP)

A lightweight, research-oriented dashboard to monitor official inflation data
and central bank inflation forecasts across selected countries.

This project is designed to be:
- Low-frequency (weekly updates)
- Free / near-zero cost
- Fully based on official or quasi-official sources
- Easy to maintain by a non-professional developer

## Covered Countries (MVP Phase)

| Country | Status | Source | Series |
|---------|--------|--------|--------|
| 🇺🇸 United States | ✅ Live | BLS API | CUSR0000SA0 (CPI-U) |
| 🇬🇧 United Kingdom | ✅ Live | FRED API | GBRCPIALLMINMEI (CPI 2015=100) |
| 🇳🇿 New Zealand | ✅ Live | Stats NZ API | CPI All Groups |

Planned expansion:
- 🇦🇺 Australia (AU)
- 🇿🇦 South Africa (ZA)

## Data Sources

### US CPI
- **Source**: Bureau of Labor Statistics (BLS)
- **Series**: CUSR0000SA0 (CPI-U All Urban Consumers)
- **Frequency**: Monthly
- **API**: https://api.bls.gov/publicAPI/v2/timeseries/data/

### UK CPI
- **Source**: FRED (Federal Reserve Economic Data)
- **Original Data**: OECD → ONS (Office for National Statistics)
- **Series**: GBRCPIALLMINMEI (CPI All Items, 2015=100)
- **Frequency**: Monthly
- **API**: https://api.stlouisfed.org/fred/series/observations
- **Note**: FRED provides more stable API than ONS direct endpoints

### NZ CPI
- **Source**: Stats NZ
- **Series**: CPI All Groups
- **Frequency**: Quarterly
- **API**: Stats NZ Open Data API

## What This Project Does

- Fetches latest headline CPI from official statistical agencies
- Calculates Year-over-Year (YoY) inflation rates
- Stores data in Supabase
- Runs weekly updates via Vercel Cron
- Detects material changes
- Sends an email notification only when changes are material

## Definition of "Material Change"

Absolute CPI change ≥ 0.3 percentage points compared to last snapshot.

## Tech Stack

- **Backend / Cron**: Vercel Serverless Functions
- **Database**: Supabase (Postgres)
- **Frontend**: Minimal Next.js page (optional)
- **Email**: Free-tier email service
- **Automation Assistant**: Claude

## Scripts

```bash
# Fetch US CPI
python3 scripts/fetch_us.py

# Fetch UK CPI
python3 scripts/fetch_uk.py

# Fetch NZ CPI
python3 scripts/fetch_nz.py
```

## Environment Variables

```
FRED_API_KEY=your_fred_api_key    # Required for UK CPI
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

---

This is a research tool, not a trading system.
