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
- Provides direct source links for every data point

**What this project does not do:**
- Provide analysis or commentary
- Make predictions
- Offer investment advice or policy recommendations

---

## Coverage

This dashboard tracks headline consumer price inflation (year-over-year) across a set of major economies:

| Economy | Inflation Measure | Source |
|-------|------------------|--------|
| United States | CPI (YoY) | U.S. Bureau of Labor Statistics (BLS) |
| China | CPI (YoY) | National Bureau of Statistics (NBS) |
| Japan | CPI (YoY) | Statistics Bureau of Japan |
| Euro Area | HICP (YoY) | Eurostat (via ECB) |
| United Kingdom | CPI (YoY) | FRED (OECD / ONS) |
| Germany | CPI (YoY) | FRED (OECD / Destatis) |
| Australia | CPI (YoY) | Australian Bureau of Statistics |
| New Zealand | CPI (YoY) | Stats NZ |
| South Africa | CPI (YoY) | FRED (OECD / Stats SA) |

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

Data is updated weekly, reflecting the most recent official releases available at the time of update.

Values may be revised by the original statistical agencies after publication.

---

## Disclaimer

This project is provided for informational purposes only.

It does not offer analysis, predictions, investment advice, or policy recommendations.  
Users should refer to the original sources for official data and methodological details.
