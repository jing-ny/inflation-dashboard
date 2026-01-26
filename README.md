# Inflation, Officially

**Official Data & Central Bank Expectations**

A lightweight, source-first monitor of inflation trends and central bank expectations across major economies.

**🔗 [View Dashboard](https://jing-ny.github.io/inflation-dashboard/)**

---

## Why This Exists

Inflation data is everywhere, but finding clean, comparable, and verifiable numbers is harder than it should be.

News headlines mix seasonally adjusted and non-adjusted figures. Commentary blends official statistics with private forecasts. Different sources use different base years, different price indices, and different reporting lags—often without saying so.

This project exists to cut through that noise. It aggregates official inflation statistics and central bank projections in one place, with clear source attribution for every number.

**What this project does:**
- Presents official CPI/HICP data from government statistics agencies
- Shows central bank inflation forecasts and targets
- Links directly to primary sources

**What this project does not do:**
- Provide analysis or commentary
- Make predictions
- Offer investment advice

---

## Scope

This dashboard tracks headline consumer price inflation (year-over-year) for nine economies:

| Country | Source | Frequency |
|---------|--------|-----------|
| 🇺🇸 United States | Bureau of Labor Statistics | Monthly |
| 🇨🇳 China | National Bureau of Statistics | Monthly |
| 🇯🇵 Japan | Statistics Bureau of Japan | Monthly |
| 🇪🇺 Euro Area | Eurostat (via ECB) | Monthly |
| 🇬🇧 United Kingdom | ONS (via OECD/FRED) | Monthly |
| 🇩🇪 Germany | Destatis (via OECD/FRED) | Monthly |
| 🇦🇺 Australia | Australian Bureau of Statistics | Quarterly |
| 🇳🇿 New Zealand | Stats NZ | Quarterly |
| 🇿🇦 South Africa | Statistics South Africa | Monthly |

Central bank forecasts are sourced from official monetary policy publications (FOMC projections, ECB staff projections, BoJ Outlook Report, etc.).

---

## Data Sources

Different countries use different official sources. This is intentional.

For some countries (US, NZ), data is fetched directly from the primary statistics agency API. For others (UK, Germany, South Africa), data comes via FRED, which aggregates OECD-harmonized series from national sources.

This approach prioritizes **stability and reproducibility** over uniformity. Each data point can be traced back to its official origin.

For full technical details, see [METHODOLOGY.md](METHODOLOGY.md).

---

## Updates

Data is updated weekly. The dashboard reflects the latest available official releases.

---

## Disclaimer

This project does not provide analysis, predictions, or investment advice. It aggregates and presents official inflation statistics and central bank projections for informational purposes only.

Always verify data with primary sources before making any decisions.

---

## Contact

Questions or suggestions? [Open an issue](https://github.com/jing-ny/inflation-dashboard/issues) on GitHub.
