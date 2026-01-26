# Methodology

Technical documentation for the Inflation Dashboard data pipeline.

---

## Overview

This dashboard aggregates official inflation statistics from government agencies and central banks across 11 economies. Data is fetched via APIs, processed into a consistent format, and displayed with full source attribution.

---

## Data Series

### Historical CPI Data

| Economy | Series ID | Source | API | Frequency | Notes |
|---------|-----------|--------|-----|-----------|-------|
| 🇺🇸 United States | `CUSR0000SA0` | Bureau of Labor Statistics | BLS API v2 | Monthly | CPI-U, All Urban Consumers, Not Seasonally Adjusted |
| 🇪🇺 Euro Area | `ICP.M.U2.N.000000.4.ANR` | European Central Bank | ECB SDMX | Monthly | HICP, Annual rate of change |
| 🇦🇺 Australia | `AUSCPIALLQINMEI` | ABS via OECD | FRED API | Quarterly | CPI, All Groups |
| 🇨🇦 Canada | `CANCPIALLMINMEI` | Statistics Canada via OECD | FRED API | Monthly | CPI, All Items |
| 🇨🇭 Switzerland | `CHECPIALLMINMEI` | FSO via OECD | FRED API | Monthly | CPI, National Index |
| 🇨🇳 China | `CHNCPIALLMINMEI` | NBS via OECD | FRED API | Monthly | CPI, All Items |
| 🇩🇪 Germany | `DEUCPIALLMINMEI` | Destatis via OECD | FRED API | Monthly | CPI, All Items |
| 🇯🇵 Japan | `CPALTT01JPM659N` | Statistics Bureau via OECD | FRED API | Monthly | CPI YoY % change (Growth rate same period previous year) |
| 🇳🇿 New Zealand | `NZLCPIALLQINMEI` | Stats NZ via OECD | FRED API | Quarterly | CPI, All Groups |
| 🇬🇧 United Kingdom | `GBRCPIALLMINMEI` | ONS via OECD | FRED API | Monthly | CPI, All Items |
| 🇿🇦 South Africa | `ZAFCPIALLMINMEI` | Stats SA via OECD | FRED API | Monthly | CPI, All Items |

**Note on Japan**: The original series `JPNCPIALLMINMEI` (COICOP 1999) was discontinued in June 2021. The dashboard now uses `JPNCPALTT01GYM659N` (COICOP 2018), which provides YoY percent change directly rather than an index value.

### IMF World Economic Outlook Forecasts

| Field | Value |
|-------|-------|
| API Endpoint | `https://www.imf.org/external/datamapper/api/v1/PCPIPCH` |
| Indicator | `PCPIPCH` — Inflation rate, average consumer prices (% change) |
| Release Schedule | April and October |
| Forecast Horizon | Current year + 5 years |

**Country Codes (ISO 3166-1 alpha-3)**:
- USA, CAN, GBR, CHE, DEU, EMU (Euro Area), AUS, NZL, ZAF, CHN, JPN

---

## API Endpoints

### FRED API
```
Base URL: https://api.stlouisfed.org/fred/series/observations
Parameters:
  - series_id: {SERIES_ID}
  - api_key: {FRED_API_KEY}
  - file_type: json
  - observation_start: {START_DATE}
```

### BLS API v2
```
Base URL: https://api.bls.gov/publicAPI/v2/timeseries/data/
Body (POST):
  - seriesid: ["CUSR0000SA0"]
  - startyear: {START_YEAR}
  - endyear: {END_YEAR}
  - registrationkey: {BLS_API_KEY} (optional)
```

### ECB SDMX
```
Base URL: https://data-api.ecb.europa.eu/service/data
Path: /ICP/M.U2.N.000000.4.ANR
Parameters:
  - format: csvdata
  - startPeriod: {YYYY-MM}
```

### IMF DataMapper
```
Base URL: https://www.imf.org/external/datamapper/api/v1
Path: /PCPIPCH/{COUNTRY_CODES}
Parameters:
  - periods: {YEAR1},{YEAR2},...
```

---

## Calculations

### Year-over-Year Inflation Rate

For series that provide index values (not already in YoY format):

```
YoY % = ((CPI_current / CPI_year_ago) - 1) × 100
```

Where:
- `CPI_current` = Index value for current period
- `CPI_year_ago` = Index value for same period one year prior

For monthly data: Compare to same month previous year  
For quarterly data: Compare to same quarter previous year

### Status vs Target

The dashboard displays status relative to central bank target:

```
Status (pp) = Current Inflation - Target Midpoint
```

Color coding:
- 🟢 **On target**: Within ±0.5pp of target
- 🟡 **Above target**: 0.5–2.0pp above target
- 🔴 **Well above target**: >2.0pp above target
- 🔵 **Below target**: >0.5pp below target

---

## Central Bank Targets

| Economy | Target | Type | Source |
|---------|--------|------|--------|
| 🇺🇸 United States | 2.0% | Point target (PCE) | Federal Reserve |
| 🇪🇺 Euro Area | 2.0% | Point target (HICP) | European Central Bank |
| 🇦🇺 Australia | 2–3% | Range | Reserve Bank of Australia |
| 🇨🇦 Canada | 1–3% | Range (midpoint 2%) | Bank of Canada |
| 🇨🇭 Switzerland | 0–2% | Price stability definition | Swiss National Bank |
| 🇨🇳 China | ~3% | Annual government target | State Council |
| 🇩🇪 Germany | 2.0% | ECB target (Euro member) | European Central Bank |
| 🇯🇵 Japan | 2.0% | Point target | Bank of Japan |
| 🇳🇿 New Zealand | 1–3% | Range (midpoint 2%) | Reserve Bank of New Zealand |
| 🇬🇧 United Kingdom | 2.0% | Point target | Bank of England |
| 🇿🇦 South Africa | 3–6% | Range (midpoint 4.5%) | South African Reserve Bank |

---

## Data Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection                          │
├─────────────────────────────────────────────────────────────┤
│  fetch_historical_cpi.py                                    │
│  ├── BLS API (US)                                          │
│  ├── ECB SDMX (Euro Area)                                  │
│  └── FRED API (UK, DE, AU, NZ, ZA, CN, JP, CA, CH)        │
│                                                             │
│  fetch_imf_forecasts.py                                     │
│  └── IMF DataMapper API                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing                               │
├─────────────────────────────────────────────────────────────┤
│  • Calculate YoY % change (for index series)               │
│  • Format dates (YYYY-MM)                                  │
│  • Round values to 1 decimal place                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output                                   │
├─────────────────────────────────────────────────────────────┤
│  data/historical_cpi.json                                  │
│  data/imf_forecasts.json                                   │
│           │                                                 │
│           ▼                                                 │
│  docs/data/ (copied for GitHub Pages)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Frontend                                 │
├─────────────────────────────────────────────────────────────┤
│  • Static HTML pages (index.html, country pages)           │
│  • Chart.js for historical visualizations                  │
│  • Vanilla JavaScript (country.js)                         │
│  • GitHub Pages hosting                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Automation

### GitHub Actions Workflow

**Schedule**: Every Monday at 7:00 AM EST (12:00 UTC)

**File**: `.github/workflows/update-data.yml`

**Steps**:
1. Checkout repository
2. Set up Python 3.11
3. Install dependencies (requests, python-dotenv)
4. Run `fetch_historical_cpi.py` (requires `FRED_API_KEY` secret)
5. Run `fetch_imf_forecasts.py` (no API key required)
6. Copy JSON files to `docs/data/`
7. Commit and push if data changed

**Required Secret**: `FRED_API_KEY`  
Get free at: https://fred.stlouisfed.org/docs/api/api_key.html

---

## File Structure

```
inflation-dashboard/
├── README.md                    # Project overview
├── METHODOLOGY.md               # This file
├── scripts/
│   ├── fetch_historical_cpi.py  # Main CPI data fetcher
│   └── fetch_imf_forecasts.py   # IMF WEO forecasts fetcher
├── data/
│   ├── historical_cpi.json      # Combined CPI data
│   └── imf_forecasts.json       # IMF forecasts
├── docs/                        # GitHub Pages root
│   ├── index.html               # Overview page
│   ├── styles.css               # Shared styles
│   ├── country.js               # Shared country page logic
│   ├── us.html, uk.html, ...    # Country detail pages
│   └── data/
│       ├── historical_cpi.json
│       └── imf_forecasts.json
└── .github/
    └── workflows/
        └── update-data.yml      # Automated weekly updates
```

---

## Known Limitations

1. **Data Lag**: OECD-sourced data via FRED may lag primary sources by days or weeks
2. **Quarterly Countries**: Australia and New Zealand data updates less frequently
3. **Central Bank Forecasts**: Currently maintained manually in `country.js`
4. **IMF Forecasts**: Only updated twice yearly (April, October)
5. **Revisions**: Historical data may be revised by source agencies

---

## Environment Variables

```bash
# Required for CPI data fetching
FRED_API_KEY=your_key_here

# Optional (increases BLS rate limits)
BLS_API_KEY=your_key_here
```

---

## Version History

| Date | Change |
|------|--------|
| Jan 2026 | Added IMF WEO forecasts integration |
| Jan 2026 | Added Canada and Switzerland |
| Jan 2026 | Fixed Japan data source (switched to COICOP 2018 series) |
| Jan 2026 | Added GitHub Actions automation |
| Jan 2026 | Initial release with 9 economies |

---

## License

MIT License — See repository for details.
