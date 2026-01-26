# Inflation, Officially

**Official Data & Central Bank Expectations**

A lightweight, source-first monitor of inflation trends and central bank expectations across major economies.

**🔗 [View Dashboard](https://jing-ny.github.io/inflation-dashboard/)**

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
- Shows IMF World Economic Outlook inflation forecasts for comparison
- Provides direct source links for every data point

**What this project does not do:**
- Provide analysis or commentary
- Make predictions
- Offer investment advice or policy recommendations

---

## Coverage

This dashboard tracks headline consumer price inflation (year-over-year) across 10 major economies:

| Economy | Inflation Measure | Primary Source | Frequency |
|---------|------------------|----------------|-----------|
| 🇺🇸 United States | CPI-U (All Urban Consumers) | Bureau of Labor Statistics via OECD/FRED | Monthly |
| 🇪🇺 Euro Area | HICP (Harmonised Index) | Eurostat via ECB | Monthly |
| 🇦🇺 Australia | CPI (All Groups) | Australian Bureau of Statistics | Quarterly |
| 🇨🇦 Canada | CPI (All Items) | Statistics Canada via OECD/FRED | Monthly |
| 🇨🇭 Switzerland | CPI (National Index) | FSO via OECD/FRED | Monthly |
| 🇨🇳 China | CPI (All Items) | National Bureau of Statistics via OECD/FRED | Monthly |
| 🇩🇪 Germany | CPI (All Items) | Destatis via OECD/FRED | Monthly |
| 🇳🇿 New Zealand | CPI (All Groups) | Stats NZ | Quarterly |
| 🇬🇧 United Kingdom | CPI (All Items) | ONS via OECD/FRED | Monthly |
| 🇿🇦 South Africa | CPI (All Items) | Stats SA via OECD/FRED | Monthly |

---

## Known Issues & High Priority Items

### 🔴 P0 — Critical (Data Accuracy)

| Issue | Description | Status |
|-------|-------------|--------|
| **US data lag** | FRED OECD series shows April 2025 data (significant lag vs BLS direct) | To fix: Switch back to BLS API or find fresher source |
| **AU/NZ data lag** | Quarterly data shows Jan 2025; may be inherent to quarterly release schedule | To verify: Check if this is expected quarterly lag |
| **Japan excluded** | FRED COICOP 1999 series discontinued June 2021; COICOP 2018 not available via FRED | To fix: Direct integration with Japan Statistics Bureau e-Stat API |
| **Broken source links** | Some central bank PDF links return 404 (PDFs moved/renamed) | To fix: Link to directory pages instead of specific PDFs |
| **Central bank forecasts stale** | Currently hardcoded in `country.js`, updated manually | To fix: Schedule monthly manual updates or automate |

### 🟡 P1 — Important (Infrastructure)

| Issue | Description | Status |
|-------|-------------|--------|
| **No forecast history** | No historical tracking of forecast changes over time | To fix: Implement Supabase backend |
| **No subscription system** | Users cannot subscribe to alerts | To fix: Build email subscription with Supabase + Resend |
| **No data freshness check** | No warning when data is older than expected | To fix: Add staleness detection and display |
| **No error monitoring** | GitHub Actions failures not reported | To fix: Add Slack/email notification on workflow failure |
| **Manual forecast updates** | Central bank forecasts require manual code changes | To fix: Move to database, build admin interface or scraper |

### 🟢 P2 — Enhancements

| Feature | Description |
|---------|-------------|
| Singapore | Add MAS / Department of Statistics data |
| India, Brazil, Mexico | Expand coverage to major emerging markets |
| Mobile optimization | Improve responsive design |
| Historical chart improvements | Add target band visualization, event markers |
| RSS feed | Alternative to email for updates |

---

## ⚠️ Important Notice

**Source links**: Some links to central bank publications may become outdated as institutions update their websites. Links point to general publication pages where possible, but specific PDF URLs may change.

**Users should always verify data against original sources before using for any official, research, or investment purposes.**

---

## Future Additions

The following economies are planned for future inclusion:

| Economy | Status | Notes |
|---------|--------|-------|
| 🇯🇵 Japan | Data source issue | FRED's OECD COICOP 1999 series discontinued June 2021; awaiting COICOP 2018 series availability or alternative API integration |
| 🇸🇬 Singapore | Planned | MAS (Monetary Authority of Singapore) / Department of Statistics |
| 🇮🇳 India | Planned | Ministry of Statistics and Programme Implementation |
| 🇧🇷 Brazil | Planned | IBGE (Brazilian Institute of Geography and Statistics) |
| 🇲🇽 Mexico | Planned | INEGI / Banco de México |

---

## Forecasts

The dashboard displays inflation forecasts from two types of sources:

**Central Bank Projections**
- Federal Reserve (FOMC SEP) — PCE inflation projections
- European Central Bank — Staff macroeconomic projections
- Bank of England — Monetary Policy Report
- Reserve Bank of Australia — Statement on Monetary Policy
- Reserve Bank of New Zealand — Monetary Policy Statement
- Bank of Canada — Monetary Policy Report
- Swiss National Bank — Conditional inflation forecast
- South African Reserve Bank — Monetary Policy Review

**IMF World Economic Outlook**
- Published twice yearly (April and October)
- Provides comparable cross-country forecasts
- Indicator: PCPIPCH (Inflation rate, average consumer prices)

Where both sources are available, the dashboard displays them side-by-side for comparison.

---

## Data Sources and Methodology

All data comes directly from official government statistics agencies or central bank publications.

Data sources are not forced into a single uniform pipeline.  
Instead, each economy uses the most stable and authoritative official source available.  
This approach prioritizes **stability and reproducibility** over uniformity.

Every figure displayed can be traced back to its original source.

For full technical details including API endpoints, series IDs, and calculation methods, see [METHODOLOGY.md](METHODOLOGY.md).

---

## Update Frequency

- **Historical CPI data**: Updated weekly (Mondays 7:00 AM EST) via GitHub Actions
- **Weekly alerts**: Sent Mondays 8:00 AM EST if material changes detected
- **IMF forecasts**: Updated when new WEO releases are published (April and October)
- **Central bank forecasts**: Updated manually following major monetary policy publications

Values may be revised by the original statistical agencies after publication.

---

## Weekly Alert

An optional email alert that notifies subscribers of material inflation changes.

**What triggers an alert:**
- YoY inflation change ≥ 0.3 percentage points, OR
- Direction reversal (rising → falling or falling → rising)

**What the alert contains:**
- Which economies had material changes
- Current YoY rate and change from previous week
- Link to the full dashboard

**What it does NOT contain:**
- Analysis or interpretation
- Predictions or forecasts
- Investment recommendations

*No analysis. No predictions. Just the data.*

---

## Disclaimer

This project is provided for informational purposes only.

It does not offer analysis, predictions, investment advice, or policy recommendations.  
Users should refer to the original sources for official data and methodological details.
