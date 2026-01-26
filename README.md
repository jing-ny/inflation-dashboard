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

This dashboard tracks headline consumer price inflation (year-over-year) across 8 major economies:

| Economy | Inflation Measure | Source | Central Bank |
|---------|-------------------|--------|--------------|
| 🇺🇸 United States | CPI (YoY) | Bureau of Labor Statistics | Federal Reserve |
| 🇪🇺 Euro Area | HICP (YoY) | Eurostat | ECB |
| 🇬🇧 United Kingdom | CPI (YoY) | ONS | Bank of England |
| 🇨🇦 Canada | CPI (YoY) | Statistics Canada | Bank of Canada |
| 🇦🇺 Australia | CPI (YoY) | ABS | RBA |
| 🇳🇿 New Zealand | CPI (YoY) | Stats NZ | RBNZ |
| 🇿🇦 South Africa | CPI (YoY) | Stats SA | SARB |
| 🇨🇳 China | CPI (YoY) | NBS | PBOC |

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

## Tech Stack

- **Frontend:** Static HTML/CSS/JavaScript (vanilla, no framework)
- **Hosting:** GitHub Pages
- **Data Fetching:** Python scripts using FRED API, IMF API
- **Automation:** GitHub Actions (weekly updates)
- **Data Storage:** JSON files

---

## Local Development

```bash
# Clone the repository
git clone https://github.com/jing-ny/inflation-dashboard.git
cd inflation-dashboard

# Set up environment
cp .env.example .env.local
# Add your FRED API key to .env.local

# Fetch latest data
python scripts/fetch_historical_cpi.py
python scripts/fetch_imf_forecasts.py
python scripts/fetch_cb_forecasts.py

# Copy data to docs
cp data/*.json docs/data/

# Serve locally
cd docs && python -m http.server 8000
# Open http://localhost:8000
```

Get a free FRED API key at: https://fred.stlouisfed.org/docs/api/api_key.html

---

## Project Structure

```
inflation-dashboard/
├── docs/                    # GitHub Pages site
│   ├── index.html           # Overview dashboard
│   ├── us.html, uk.html...  # Country pages
│   ├── styles.css           # Styles
│   ├── country.js           # Shared JavaScript
│   └── data/                # JSON data files
├── scripts/                 # Python data fetchers
├── data/                    # Raw data output
├── METHODOLOGY.md           # Technical documentation
└── PROJECT_PLAN.md          # Architecture reference
```

---

## Disclaimer

This project is provided for informational purposes only.

It does not offer analysis, predictions, investment advice, or policy recommendations.  
Users should refer to the original sources for official data and methodological details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Contact

Questions or suggestions? [Open an issue](https://github.com/jing-ny/inflation-dashboard/issues) on GitHub.
