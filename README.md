# Inflation, Officially

**Official Data & Central Bank Expectations**

A lightweight, source-first monitor of inflation trends and central bank expectations across major economies.

🔗 **Live Dashboard:** https://jing-ny.github.io/inflation-dashboard/

---

## Why This Exists

Inflation data is everywhere, but it is often difficult to interpret in a consistent way.  
Figures are reported using different definitions, released on different schedules, and frequently mixed with commentary or opinion.

This project exists to cut through that noise.

It aggregates official inflation statistics and central bank projections in one place, with clear source attribution for every number, making cross-country comparison easier and more transparent.

---

## What This Project Does (and Does Not Do)

**What this project does:**

- Collects headline CPI inflation data from official government statistics agencies
- Displays central bank inflation expectations and projections where available
- Compares central bank forecasts with IMF World Economic Outlook projections
- Provides direct source links for every data point

**What this project does not do:**

- Provide analysis or commentary
- Make predictions
- Offer investment advice or policy recommendations

---

## Coverage

This dashboard tracks headline consumer price inflation (year-over-year) across 13 economies:

| Economy | Inflation Measure | Source | Central Bank |
|---------|-------------------|--------|--------------|
| 🇺🇸 United States | CPI (YoY) | Bureau of Labor Statistics | Federal Reserve |
| 🇪🇺 Euro Area | HICP (YoY) | Eurostat | ECB |
| 🇬🇧 United Kingdom | CPI (YoY) | ONS | Bank of England |
| 🇨🇦 Canada | CPI (YoY) | Statistics Canada | Bank of Canada |
| 🇦🇺 Australia | CPI (YoY) | ABS | RBA |
| 🇳🇿 New Zealand | CPI (YoY) | Stats NZ | RBNZ |
| 🇿🇦 South Africa | CPI (YoY) | Stats SA | SARB |
| 🇯🇵 Japan | CPI (YoY) | Statistics Bureau | Bank of Japan |
| 🇰🇷 South Korea | CPI (YoY) | KOSTAT | Bank of Korea |
| 🇸🇬 Singapore | CPI (YoY) | DOS | MAS |
| 🇮🇳 India | CPI (YoY) | MOSPI | RBI |
| 🇨🇳 China | CPI (YoY) | NBS | PBOC |
| 🇻🇪 Venezuela | CPI (YoY) | BCV | BCV |

---

## Data Sources and Methodology

All data comes directly from official government statistics agencies or central bank publications.

Data sources are not forced into a single uniform pipeline.  
Instead, each economy uses the most stable and authoritative official source available.  
This approach prioritizes **stability and reproducibility** over uniformity.

Every figure displayed can be traced back to its original source.

For detailed methodology, see [METHODOLOGY.md](METHODOLOGY.md).

---

## Update Frequency

- **CPI Data:** Updated weekly, reflecting the most recent official releases
- **Central Bank Forecasts:** Updated after major monetary policy meetings
- **IMF Forecasts:** Updated twice yearly (April and October WEO releases)

Values may be revised by the original statistical agencies after publication.

---

## Data Architecture

All data is stored in `docs/data/` as the single source of truth:

```
docs/data/
├── historical_cpi.json       # CPI history for all 13 countries
├── cb_forecasts.json         # Central bank inflation forecasts
├── imf_forecasts.json        # IMF WEO projections
├── cpi_supplements.json      # Manual supplements for lagging FRED data
└── history/                  # Forecast revision tracking
```

### Manual Update Tools

For monthly CPI updates:
```bash
# Update a single country
python3 update_cpi.py -c US -d 2026-01 -v 2.8

# View current data
python3 update_cpi.py --show-all

# Batch update multiple countries
python3 batch_update_cpi.py --dry-run
```

See [CPI_UPDATE_GUIDE.md](CPI_UPDATE_GUIDE.md) for detailed update procedures.

---

## Tech Stack

- **Frontend:** Static HTML/CSS/JavaScript (vanilla, no framework)
- **Hosting:** GitHub Pages
- **Data Fetching:** Python scripts using FRED API
- **Automation:** GitHub Actions (twice weekly checks)
- **Data Storage:** JSON files in `docs/data/`

---

## Local Development

```bash
# Clone the repository
git clone https://github.com/jing-ny/inflation-dashboard.git
cd inflation-dashboard

# View current CPI data
python3 update_cpi.py --show-all

# Start a local server
python3 -m http.server 8000 --directory docs
# Open http://localhost:8000
```

---

## Changelog

### February 2026
- **Data Quality Fix:** Corrected Dec 2025 CPI values for 8 countries using verified official sources
- **Architecture:** Consolidated all data to `docs/data/` (single source of truth)
- **Tooling:** Added `update_cpi.py` and `batch_update_cpi.py` for manual updates
- **Documentation:** Added `CPI_UPDATE_GUIDE.md` with official source URLs and release schedules

### January 2026
- Added 5 new countries: South Korea, Singapore, India, China, Venezuela
- Implemented central bank forecast tracking
- Added IMF WEO forecast comparison
- Set up automated monitoring via GitHub Actions

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.
